import { describe, expect, it, vi, beforeEach } from 'vitest';
import { createTelemetryPipeline } from './pipeline';
import { createEventBus, type NjzEventMap } from '@njz-os/core';

beforeEach(() => {
  vi.useRealTimers();
});

describe('telemetry pipeline', () => {
  it('track + flush sends a single batch', async () => {
    const posted: unknown[][] = [];
    const post = vi.fn(async (batch: unknown[]) => {
      posted.push(batch);
    });
    const p = createTelemetryPipeline({ post, flushIntervalMs: 60_000 });
    p.track('a', { x: 1 });
    p.track('b', { y: 2 });
    await p.flush();
    expect(posted).toHaveLength(1);
    expect((posted[0] as Array<{ name: string }>).map((e) => e.name)).toEqual(['a', 'b']);
    p.stop();
  });

  it('scrubs default PII keys', async () => {
    const posted: unknown[][] = [];
    const p = createTelemetryPipeline({
      post: async (batch) => void posted.push(batch),
      flushIntervalMs: 60_000,
    });
    p.track('signup', { email: 'a@b.com', displayName: 'Alice', tier: 'free' });
    await p.flush();
    const payload = (posted[0]?.[0] as { payload: Record<string, string> }).payload;
    expect(payload.email).toBe('[scrubbed]');
    expect(payload.displayName).toBe('[scrubbed]');
    expect(payload.tier).toBe('free');
    p.stop();
  });

  it('scrubs free-form email addresses by pattern', async () => {
    const posted: unknown[][] = [];
    const p = createTelemetryPipeline({
      post: async (batch) => void posted.push(batch),
      flushIntervalMs: 60_000,
    });
    p.track('note', { freeText: 'reach me at me@x.com please', tier: 'free' });
    await p.flush();
    const payload = (posted[0]?.[0] as { payload: Record<string, string> }).payload;
    expect(payload.freeText).toBe('[scrubbed:email]');
    p.stop();
  });

  it('drops oldest event when ring overflows', async () => {
    const posted: unknown[][] = [];
    const p = createTelemetryPipeline({
      post: async (batch) => void posted.push(batch),
      flushIntervalMs: 60_000,
      ringCapacity: 3,
    });
    p.track('a', {});
    p.track('b', {});
    p.track('c', {});
    p.track('d', {});
    expect(p.stats().dropped).toBe(1);
    await p.flush();
    expect((posted[0] as Array<{ name: string }>).map((e) => e.name)).toEqual(['b', 'c', 'd']);
    p.stop();
  });

  it('failed post re-enqueues batch and counts failure', async () => {
    let calls = 0;
    const p = createTelemetryPipeline({
      post: async () => {
        calls += 1;
        throw new Error('network');
      },
      flushIntervalMs: 60_000,
    });
    p.track('a', {});
    await p.flush();
    expect(calls).toBe(1);
    expect(p.stats().queued).toBe(1);
    expect(p.stats().failed).toBe(1);
    p.stop();
  });

  it('bridges progression.event from the bus through track()', async () => {
    const bus = createEventBus<NjzEventMap>();
    const posted: unknown[][] = [];
    const p = createTelemetryPipeline({
      post: async (batch) => void posted.push(batch),
      flushIntervalMs: 60_000,
      bus,
    });
    bus.emit('progression.event', {
      kind: 'session.start',
      userId: 'u_1' as unknown as never,
      sessionId: 's_1' as unknown as never,
      module: 'focus-hero',
      at: '2026-05-30T00:00:00.000Z',
    });
    await p.flush();
    const names = (posted[0] as Array<{ name: string }>).map((e) => e.name);
    expect(names).toContain('progression.session.start');
    p.stop();
  });

  it('flush respects maxBatchSize', async () => {
    const posted: unknown[][] = [];
    const p = createTelemetryPipeline({
      post: async (batch) => void posted.push(batch),
      flushIntervalMs: 60_000,
      maxBatchSize: 2,
    });
    p.track('a', {});
    p.track('b', {});
    p.track('c', {});
    await p.flush();
    await p.flush();
    expect(posted).toHaveLength(2);
    expect(posted[0]).toHaveLength(2);
    expect(posted[1]).toHaveLength(1);
    p.stop();
  });
});
