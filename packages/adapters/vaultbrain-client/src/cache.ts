/**
 * PRX-25-ENH-01 — IndexedDB hot-cache for vaultbrain reads.
 *
 * Read-through cache with per-resource TTL. Cache-bust on the
 * default event bus when a downstream mutation event arrives. Backed by
 * `idb-keyval` for browser persistence; falls back to an in-memory Map
 * in Node / SSR environments.
 *
 * Used inside the VaultbrainClient to make warm boots feel instant
 * (< 50 ms to first useful render of /learn, /write, /brain home
 * views per PRX-25-ENH-01 acceptance criteria).
 */

import { defaultEventBus } from '@njz-os/core';
import { createStore, get, set, del } from 'idb-keyval';

export type CacheKind = 'profile' | 'progression' | 'manuscript' | 'cards';

export const DEFAULT_TTL_MS: Record<CacheKind, number> = {
  profile: 5 * 60_000,
  progression: 60_000,
  manuscript: 10 * 60_000,
  cards: 5 * 60_000,
};

export interface CacheEntry<T> {
  value: T;
  storedAt: number;
  ttlMs: number;
}

export interface CacheStore {
  get<T>(key: string): Promise<CacheEntry<T> | null>;
  set<T>(key: string, value: T, ttlMs: number): Promise<void>;
  del(key: string): Promise<void>;
  clear(): Promise<void>;
}

export function isBrowser(): boolean {
  return typeof globalThis !== 'undefined' && typeof (globalThis as { indexedDB?: unknown }).indexedDB !== 'undefined';
}

export function createMemoryCacheStore(): CacheStore {
  const store = new Map<string, CacheEntry<unknown>>();
  return {
    async get<T>(key: string): Promise<CacheEntry<T> | null> {
      const entry = store.get(key);
      return (entry as CacheEntry<T> | undefined) ?? null;
    },
    async set<T>(key: string, value: T, ttlMs: number): Promise<void> {
      store.set(key, { value, storedAt: Date.now(), ttlMs });
    },
    async del(key: string): Promise<void> {
      store.delete(key);
    },
    async clear(): Promise<void> {
      store.clear();
    },
  };
}

export function createIdbCacheStore(dbName = 'njz-vaultbrain-cache'): CacheStore {
  const idbStore = createStore(dbName, 'kv');
  return {
    async get<T>(key: string): Promise<CacheEntry<T> | null> {
      const entry = (await get(key, idbStore)) as CacheEntry<T> | undefined;
      return entry ?? null;
    },
    async set<T>(key: string, value: T, ttlMs: number): Promise<void> {
      await set(key, { value, storedAt: Date.now(), ttlMs }, idbStore);
    },
    async del(key: string): Promise<void> {
      await del(key, idbStore);
    },
    async clear(): Promise<void> {
      throw new Error('clear not implemented for idb-keyval store; del individual keys');
    },
  };
}

export function createCacheStore(): CacheStore {
  return isBrowser() ? createIdbCacheStore() : createMemoryCacheStore();
}

export function isFresh(entry: CacheEntry<unknown> | null, nowMs = Date.now()): boolean {
  if (!entry) return false;
  return nowMs - entry.storedAt < entry.ttlMs;
}

export function cacheKey(kind: CacheKind, ...parts: string[]): string {
  return [kind, ...parts].join(':');
}

/**
 * Wire the default event bus to invalidate cache keys when downstream
 * mutations land. Pass `store` so this can target a specific cache
 * instance (avoids global mutable state).
 */
export function attachCacheBus(store: CacheStore): () => void {
  const unsubProgression = defaultEventBus.on('progression.event', (event) => {
    void store.del(cacheKey('progression', event.userId as unknown as string));
  });
  return () => {
    unsubProgression();
  };
}
