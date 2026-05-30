import { describe, expect, it } from 'vitest';
import {
  cacheKey,
  createMemoryCacheStore,
  isBrowser,
  isFresh,
  DEFAULT_TTL_MS,
} from './cache';

describe('cache primitives', () => {
  it('cacheKey joins kind + parts with colons', () => {
    expect(cacheKey('profile', 'me')).toBe('profile:me');
    expect(cacheKey('progression', 'u_1')).toBe('progression:u_1');
    expect(cacheKey('manuscript', 'u_1', 'm_1')).toBe('manuscript:u_1:m_1');
  });

  it('isFresh respects ttl + storedAt', () => {
    const now = 1_000_000;
    expect(isFresh({ value: 'a', storedAt: now - 5_000, ttlMs: 10_000 }, now)).toBe(true);
    expect(isFresh({ value: 'a', storedAt: now - 15_000, ttlMs: 10_000 }, now)).toBe(false);
    expect(isFresh(null)).toBe(false);
  });

  it('memory store round-trips a value', async () => {
    const store = createMemoryCacheStore();
    await store.set('k', { x: 1 }, 60_000);
    const entry = await store.get<{ x: number }>('k');
    expect(entry?.value).toEqual({ x: 1 });
    expect(entry?.ttlMs).toBe(60_000);
  });

  it('memory store del removes the key', async () => {
    const store = createMemoryCacheStore();
    await store.set('k', 1, 60_000);
    await store.del('k');
    expect(await store.get('k')).toBeNull();
  });

  it('isBrowser is false in Node test environment', () => {
    expect(isBrowser()).toBe(false);
  });

  it('DEFAULT_TTL_MS uses sensible orders of magnitude', () => {
    expect(DEFAULT_TTL_MS.progression).toBeLessThan(DEFAULT_TTL_MS.profile);
    expect(DEFAULT_TTL_MS.profile).toBeLessThan(DEFAULT_TTL_MS.manuscript);
  });
});
