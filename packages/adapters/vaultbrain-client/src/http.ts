/**
 * PRX-25-EPIC-01 — HTTP transport layer.
 *
 * Thin wrapper around `fetch` with: bearer-token injection, abort
 * signal support, configurable retry (capped exponential backoff),
 * observability events to the default bus, schema-parse on every
 * response (caller-provided schema).
 *
 * Failures become typed errors:
 *   - `VaultbrainNetworkError` — connection refused, DNS, abort
 *   - `VaultbrainHttpError` — non-2xx response
 *   - `VaultbrainContractError` — response failed the zod schema
 */

import type { ZodTypeAny, z } from 'zod';
import { defaultEventBus } from '@njz-os/core';
import { uuidV7 } from './queue';

export interface HttpClientConfig {
  baseUrl: string;
  bearerToken: () => string | Promise<string>;
  fetchImpl?: typeof fetch;
  retry?: {
    maxAttempts: number;
    initialDelayMs: number;
    maxDelayMs: number;
  };
}

export interface HttpCallOptions<S extends ZodTypeAny> {
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  path: string;
  body?: unknown;
  responseSchema: S;
  signal?: AbortSignal;
  isIdempotent?: boolean;
}

export class VaultbrainNetworkError extends Error {
  public readonly retryable: boolean;
  constructor(message: string, cause: unknown, retryable: boolean = true) {
    super(message, { cause });
    this.name = 'VaultbrainNetworkError';
    this.retryable = retryable;
  }
}

export class VaultbrainHttpError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly retryable: boolean
  ) {
    super(message);
    this.name = 'VaultbrainHttpError';
  }
}

export class VaultbrainContractError extends Error {
  constructor(
    message: string,
    public readonly issues: unknown
  ) {
    super(message);
    this.name = 'VaultbrainContractError';
  }
}

const DEFAULT_RETRY = {
  maxAttempts: 4,
  initialDelayMs: 500,
  maxDelayMs: 8_000,
};

function isRetryableStatus(status: number): boolean {
  return status === 408 || status === 429 || (status >= 500 && status < 600);
}

async function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new Error('aborted'));
      return;
    }
    const timer = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort);
      resolve();
    }, ms);
    const onAbort = (): void => {
      clearTimeout(timer);
      reject(new Error('aborted'));
    };
    signal?.addEventListener('abort', onAbort, { once: true });
  });
}

export interface HttpClient {
  call<S extends ZodTypeAny>(opts: HttpCallOptions<S>): Promise<z.infer<S>>;
}

export function createHttpClient(config: HttpClientConfig): HttpClient {
  const fetchImpl = config.fetchImpl ?? globalThis.fetch;
  if (!fetchImpl) {
    throw new Error(
      'No fetch implementation available. Pass `fetchImpl` in HttpClientConfig.'
    );
  }
  const retry = config.retry ?? DEFAULT_RETRY;

  return {
    async call<S extends ZodTypeAny>(opts: HttpCallOptions<S>): Promise<z.infer<S>> {
      const requestId = uuidV7();
      const url = config.baseUrl.replace(/\/$/, '') + opts.path;
      const token = await config.bearerToken();
      const headers: Record<string, string> = {
        accept: 'application/json',
        authorization: `Bearer ${token}`,
        'x-request-id': requestId,
      };
      const init: RequestInit = {
        method: opts.method,
        headers,
        signal: opts.signal,
      };
      if (opts.body !== undefined) {
        headers['content-type'] = 'application/json';
        init.body = JSON.stringify(opts.body);
      }

      defaultEventBus.emit('vaultbrain-client.request', {
        method: opts.method,
        url,
        requestId,
      });

      let lastErr: unknown = null;
      const startedAt = Date.now();
      const maxAttempts = opts.method === 'GET' || opts.isIdempotent
        ? retry.maxAttempts
        : 1;

      for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
        try {
          const res = await fetchImpl(url, init);
          const durationMs = Date.now() - startedAt;
          defaultEventBus.emit('vaultbrain-client.response', {
            requestId,
            status: res.status,
            durationMs,
          });
          if (!res.ok) {
            const retryable = isRetryableStatus(res.status);
            const err = new VaultbrainHttpError(
              `vaultbrain ${opts.method} ${opts.path} → ${res.status}`,
              res.status,
              retryable
            );
            if (retryable && attempt < maxAttempts) {
              lastErr = err;
              const delay = Math.min(
                retry.initialDelayMs * 2 ** (attempt - 1),
                retry.maxDelayMs
              );
              await sleep(delay, opts.signal);
              continue;
            }
            defaultEventBus.emit('vaultbrain-client.error', { requestId, err });
            throw err;
          }
          const json = res.status === 204 ? null : await res.json();
          const parsed = opts.responseSchema.safeParse(json);
          if (!parsed.success) {
            const err = new VaultbrainContractError(
              `vaultbrain ${opts.method} ${opts.path} → response failed schema`,
              parsed.error.issues
            );
            defaultEventBus.emit('vaultbrain-client.error', { requestId, err });
            throw err;
          }
          return parsed.data as z.infer<S>;
        } catch (err) {
          if (
            err instanceof VaultbrainHttpError ||
            err instanceof VaultbrainContractError
          ) {
            throw err;
          }
          lastErr = err;
          const netErr = new VaultbrainNetworkError(
            `vaultbrain ${opts.method} ${opts.path} — network failure`,
            err,
            true
          );
          if (attempt < maxAttempts) {
            const delay = Math.min(
              retry.initialDelayMs * 2 ** (attempt - 1),
              retry.maxDelayMs
            );
            await sleep(delay, opts.signal);
            continue;
          }
          defaultEventBus.emit('vaultbrain-client.error', {
            requestId,
            err: netErr,
          });
          throw netErr;
        }
      }
      throw lastErr ?? new Error('unreachable retry loop exit');
    },
  };
}
