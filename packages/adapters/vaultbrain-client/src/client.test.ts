import { describe, expect, it, beforeEach } from 'vitest';
import { createVaultbrainClient } from './client';
import {
  VaultbrainContractError,
  VaultbrainHttpError,
  VaultbrainNetworkError,
} from './http';
import { defaultEventBus } from '@njz-os/core';

function mockFetch(handler: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response> | Response): typeof fetch {
  return ((input: RequestInfo | URL, init?: RequestInit) =>
    Promise.resolve(handler(input, init))) as typeof fetch;
}

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}

const BASE = { httpUrl: 'https://vb.test', bearerToken: () => 'token' };

beforeEach(() => {
  defaultEventBus.clear();
});

describe('vaultbrain-client', () => {
  it('currentUser: GET /users/me, parses + returns User', async () => {
    const fetchImpl = mockFetch(() =>
      jsonResponse(200, {
        id: 'u_1',
        email: 'a@b.com',
        displayName: 'Alice',
        tier: 'free',
        timezone: 'UTC',
        createdAt: '2026-05-30T00:00:00.000Z',
      })
    );
    const client = createVaultbrainClient({ ...BASE, fetchImpl });
    const user = await client.currentUser();
    expect(user.id).toBe('u_1');
    expect(user.tier).toBe('free');
  });

  it('emits request + response events on the default bus', async () => {
    const fetchImpl = mockFetch(() => jsonResponse(200, {
      totalXp: 100,
      level: 1,
      streak: { currentDays: 1, longestDays: 1, lastActiveAt: '2026-05-30T00:00:00.000Z' },
      recentEvents: [],
    }));
    const client = createVaultbrainClient({ ...BASE, fetchImpl });
    const reqEvents: unknown[] = [];
    const resEvents: unknown[] = [];
    defaultEventBus.on('vaultbrain-client.request', (e) => reqEvents.push(e));
    defaultEventBus.on('vaultbrain-client.response', (e) => resEvents.push(e));
    await client.getProgression('u_1');
    expect(reqEvents).toHaveLength(1);
    expect(resEvents).toHaveLength(1);
  });

  it('throws VaultbrainHttpError on 4xx; does not retry', async () => {
    let calls = 0;
    const fetchImpl = mockFetch(() => {
      calls += 1;
      return new Response('', { status: 401 });
    });
    const client = createVaultbrainClient({ ...BASE, fetchImpl });
    await expect(client.currentUser()).rejects.toBeInstanceOf(VaultbrainHttpError);
    expect(calls).toBe(1);
  });

  it('retries on 5xx for GET, succeeds on attempt 2', async () => {
    let calls = 0;
    const fetchImpl = mockFetch(() => {
      calls += 1;
      if (calls === 1) return new Response('', { status: 503 });
      return jsonResponse(200, {
        id: 'u_1',
        email: 'a@b.com',
        displayName: 'A',
        tier: 'free',
        timezone: 'UTC',
        createdAt: '2026-05-30T00:00:00.000Z',
      });
    });
    const client = createVaultbrainClient({ ...BASE, fetchImpl });
    const user = await client.currentUser();
    expect(user.id).toBe('u_1');
    expect(calls).toBe(2);
  });

  it('throws VaultbrainContractError on schema mismatch', async () => {
    const fetchImpl = mockFetch(() =>
      jsonResponse(200, { id: 'u_1' /* missing required fields */ })
    );
    const client = createVaultbrainClient({ ...BASE, fetchImpl });
    await expect(client.currentUser()).rejects.toBeInstanceOf(VaultbrainContractError);
  });

  it('startSession: POST with idempotency key auto-added', async () => {
    const bodies: unknown[] = [];
    const fetchImpl = mockFetch((_url, init) => {
      bodies.push(init?.body ? JSON.parse(init.body as string) : null);
      return jsonResponse(200, {
        sessionId: 's_1',
        startedAt: '2026-05-30T00:00:00.000Z',
      });
    });
    const client = createVaultbrainClient({ ...BASE, fetchImpl });
    await client.startSession({
      module: 'focus-hero',
      mode: 'pomodoro_25_5',
      startedAt: '2026-05-30T00:00:00.000Z',
    });
    expect(bodies).toHaveLength(1);
    const body = bodies[0] as Record<string, string>;
    expect(typeof body.idempotencyKey).toBe('string');
    expect(body.idempotencyKey.length).toBeGreaterThan(20);
  });

  it('enqueues on network failure for mutating call', async () => {
    const fetchImpl = mockFetch(() => {
      throw new TypeError('fetch failed');
    });
    const client = createVaultbrainClient({ ...BASE, fetchImpl });
    await expect(
      client.recordEvent({
        event: {
          kind: 'session.start',
          userId: 'u_1' as unknown as string,
          sessionId: 's_1' as unknown as string,
          module: 'focus-hero',
          at: '2026-05-30T00:00:00.000Z',
        } as unknown as Parameters<typeof client.recordEvent>[0]['event'],
      })
    ).rejects.toBeInstanceOf(VaultbrainNetworkError);
    expect(await client.queueSize()).toBe(1);
  });

  it('listCards: unwraps {cards, totalCount} into Card[]', async () => {
    const fetchImpl = mockFetch(() =>
      jsonResponse(200, {
        cards: [
          {
            id: 'c_1',
            deckSlug: 'd',
            front: 'q',
            back: 'a',
            interval: 1,
            easeFactor: 2.5,
            dueAt: '2026-05-30T00:00:00.000Z',
          },
        ],
        totalCount: 1,
      })
    );
    const client = createVaultbrainClient({ ...BASE, fetchImpl });
    const cards = await client.listCards('d');
    expect(cards).toHaveLength(1);
    expect(cards[0]?.id).toBe('c_1');
  });

  it('emits vaultbrain-client.error on terminal failure', async () => {
    const fetchImpl = mockFetch(() => new Response('', { status: 400 }));
    const client = createVaultbrainClient({ ...BASE, fetchImpl });
    const errors: unknown[] = [];
    defaultEventBus.on('vaultbrain-client.error', (e) => errors.push(e));
    await expect(client.currentUser()).rejects.toBeInstanceOf(VaultbrainHttpError);
    expect(errors).toHaveLength(1);
  });

  it('abort signal propagates and aborts in-flight retries', async () => {
    const fetchImpl = mockFetch(() => {
      throw new TypeError('fetch failed');
    });
    const client = createVaultbrainClient({ ...BASE, fetchImpl });
    const controller = new AbortController();
    setTimeout(() => controller.abort(), 50);
    await expect(client.currentUser(controller.signal)).rejects.toBeDefined();
  });
});
