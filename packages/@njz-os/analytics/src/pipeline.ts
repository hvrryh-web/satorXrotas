/**
 * PRX-25-PATCH-04 — Unified telemetry pipeline.
 *
 * Batched, fire-and-forget analytics:
 *
 *   const pipeline = createTelemetryPipeline({
 *     flushIntervalMs: 5_000,
 *     maxBatchSize: 100,
 *     post: async (batch) => fetch('/events/batch', {...}),
 *   });
 *   pipeline.track('focus.session.start', { module: 'focus-hero', ... });
 *
 * The ring buffer caps at 200 events — overflow increments a counter
 * for visibility (use case: bursts during onboarding). Flushes:
 *   - every `flushIntervalMs` (interval timer)
 *   - on `pagehide` via `sendBeacon` (best-effort terminal flush)
 *   - on explicit `flush()`
 *
 * PII scrubber runs *before* the batch leaves the browser; the
 * `scrubbers` config lets each consumer add module-specific scrubbers.
 */

import type { NjzEventMap, EventBus } from '@njz-os/core';

export interface TelemetryEvent {
  name: string;
  payload: Record<string, unknown>;
  occurredAt: string;
}

export interface TelemetryPipelineConfig {
  flushIntervalMs?: number;
  maxBatchSize?: number;
  ringCapacity?: number;
  post: (batch: TelemetryEvent[]) => Promise<void>;
  scrubbers?: Array<(event: TelemetryEvent) => TelemetryEvent>;
  bus?: EventBus<NjzEventMap>;
  beaconUrl?: string;
}

export interface TelemetryPipeline {
  track(name: string, payload: Record<string, unknown>): void;
  flush(): Promise<void>;
  stop(): void;
  stats(): { queued: number; dropped: number; flushed: number; failed: number };
}

const DEFAULT_PII_KEYS = [
  'email',
  'password',
  'token',
  'authorization',
  'displayName',
  'manuscriptBody',
  'cardFront',
  'cardBack',
  'body',
];

const PII_KEYS_LOWER = new Set(DEFAULT_PII_KEYS.map((k) => k.toLowerCase()));

function defaultScrubber(event: TelemetryEvent): TelemetryEvent {
  const cleaned: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(event.payload)) {
    const keyLower = k.toLowerCase();
    if (PII_KEYS_LOWER.has(keyLower)) {
      cleaned[k] = '[scrubbed]';
    } else if (
      typeof v === 'string' &&
      /[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/i.test(v)
    ) {
      cleaned[k] = '[scrubbed:email]';
    } else {
      cleaned[k] = v;
    }
  }
  return { ...event, payload: cleaned };
}

export function createTelemetryPipeline(
  config: TelemetryPipelineConfig
): TelemetryPipeline {
  const flushIntervalMs = config.flushIntervalMs ?? 5_000;
  const maxBatchSize = config.maxBatchSize ?? 50;
  const ringCapacity = config.ringCapacity ?? 200;
  const scrubbers = [defaultScrubber, ...(config.scrubbers ?? [])];

  const ring: TelemetryEvent[] = [];
  let dropped = 0;
  let flushed = 0;
  let failed = 0;

  const apply = (event: TelemetryEvent): TelemetryEvent => {
    let current = event;
    for (const fn of scrubbers) current = fn(current);
    return current;
  };

  const flush = async (): Promise<void> => {
    if (ring.length === 0) return;
    const batch = ring.splice(0, maxBatchSize);
    try {
      await config.post(batch);
      flushed += batch.length;
    } catch {
      ring.unshift(...batch);
      failed += 1;
    }
  };

  let timer: ReturnType<typeof setInterval> | null = setInterval(flush, flushIntervalMs);

  const onPageHide = (): void => {
    if (ring.length === 0) return;
    if (
      typeof navigator !== 'undefined' &&
      'sendBeacon' in navigator &&
      config.beaconUrl
    ) {
      try {
        const ok = navigator.sendBeacon(
          config.beaconUrl,
          new Blob([JSON.stringify(ring.splice(0, ring.length))], {
            type: 'application/json',
          })
        );
        if (ok) flushed += 1;
      } catch {
        failed += 1;
      }
    } else {
      void flush();
    }
  };

  const hasWindow =
    typeof globalThis !== 'undefined' &&
    typeof (globalThis as { addEventListener?: unknown }).addEventListener ===
      'function';
  if (hasWindow) {
    (globalThis as unknown as Window).addEventListener?.('pagehide', onPageHide);
  }

  const stop = (): void => {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
    if (hasWindow) {
      (globalThis as unknown as Window).removeEventListener?.(
        'pagehide',
        onPageHide
      );
    }
  };

  // Optional bridge: forward progression events through the pipeline.
  let unsub: (() => void) | null = null;
  if (config.bus) {
    unsub = config.bus.on('progression.event', (event) => {
      const payload = { ...(event as unknown as Record<string, unknown>) };
      track(`progression.${event.kind}`, payload);
    });
  }

  function track(name: string, payload: Record<string, unknown>): void {
    const event = apply({
      name,
      payload,
      occurredAt: new Date().toISOString(),
    });
    if (ring.length >= ringCapacity) {
      ring.shift();
      dropped += 1;
    }
    ring.push(event);
  }

  return {
    track,
    flush,
    stop: () => {
      stop();
      if (unsub) unsub();
    },
    stats: () => ({ queued: ring.length, dropped, flushed, failed }),
  };
}
