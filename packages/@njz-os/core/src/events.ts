/**
 * PRX-25-PATCH-01 — Standardised event-emitter surface.
 *
 * One canonical, type-safe EventBus consumed by every module engine
 * (focus, audio, polyworld, blocker, writing, learning-cards,
 * brain-training, analytics) so cross-lane subscribers share a single
 * surface.
 *
 * Design choices:
 *   - Synchronous dispatch by default — predictable order, easy to test.
 *   - Each subscribe call returns its own unsubscribe; never use indexes.
 *   - Listener errors are isolated; one throwing listener does not kill
 *     the remaining listeners for that event.
 *   - The bus is type-parameterised by an event map; subscribers can only
 *     subscribe to named events and receive the correctly-typed payload.
 *   - One shared default bus instance lives at `defaultEventBus` so every
 *     module participates in the same broadcast unless explicitly given
 *     its own bus (test isolation).
 */

import type { ProgressionEvent } from './progression';

/* eslint-disable @typescript-eslint/no-explicit-any */

export interface EventBus<EventMap extends Record<string, unknown>> {
  on<K extends keyof EventMap>(
    event: K,
    listener: (payload: EventMap[K]) => void
  ): () => void;
  off<K extends keyof EventMap>(
    event: K,
    listener: (payload: EventMap[K]) => void
  ): void;
  emit<K extends keyof EventMap>(event: K, payload: EventMap[K]): void;
  clear<K extends keyof EventMap>(event?: K): void;
  listenerCount<K extends keyof EventMap>(event: K): number;
  setErrorHandler(handler: (err: unknown, event: keyof EventMap) => void): void;
}

export function createEventBus<EventMap extends Record<string, unknown>>(): EventBus<EventMap> {
  const listeners = new Map<keyof EventMap, Set<(payload: any) => void>>();
  let errorHandler: (err: unknown, event: keyof EventMap) => void = (err) => {
    if (typeof console !== 'undefined' && typeof console.error === 'function') {
      console.error('[EventBus listener error]', err);
    }
  };

  const on: EventBus<EventMap>['on'] = (event, listener) => {
    let bucket = listeners.get(event);
    if (!bucket) {
      bucket = new Set();
      listeners.set(event, bucket);
    }
    bucket.add(listener as (payload: any) => void);
    return () => {
      const b = listeners.get(event);
      b?.delete(listener as (payload: any) => void);
      if (b && b.size === 0) listeners.delete(event);
    };
  };

  const off: EventBus<EventMap>['off'] = (event, listener) => {
    const bucket = listeners.get(event);
    if (!bucket) return;
    bucket.delete(listener as (payload: any) => void);
    if (bucket.size === 0) listeners.delete(event);
  };

  const emit: EventBus<EventMap>['emit'] = (event, payload) => {
    const bucket = listeners.get(event);
    if (!bucket) return;
    const snapshot = Array.from(bucket);
    for (const listener of snapshot) {
      try {
        listener(payload);
      } catch (err) {
        errorHandler(err, event);
      }
    }
  };

  const clear: EventBus<EventMap>['clear'] = (event) => {
    if (event === undefined) listeners.clear();
    else listeners.delete(event);
  };

  const listenerCount: EventBus<EventMap>['listenerCount'] = (event) =>
    listeners.get(event)?.size ?? 0;

  const setErrorHandler: EventBus<EventMap>['setErrorHandler'] = (handler) => {
    errorHandler = handler;
  };

  return { on, off, emit, clear, listenerCount, setErrorHandler };
}

/**
 * Canonical NJZ RAT-OS event map.
 *
 * Adding a new event:
 *   1. Add the entry below with its payload type.
 *   2. Reference it from .agents/SCHEMA_REGISTRY.md (Event section).
 *   3. Emit it from the producing module; subscribe from the consuming module.
 *   4. Land tests on both sides in the same PR.
 *
 * Removing an event: same protocol but in reverse, plus a DECISION_LOG line.
 */
export type NjzEventMap = {
  'progression.event': ProgressionEvent;
  'vaultbrain-client.request': {
    method: string;
    url: string;
    requestId: string;
  };
  'vaultbrain-client.response': {
    requestId: string;
    status: number;
    durationMs: number;
  };
  'vaultbrain-client.error': {
    requestId: string;
    err: unknown;
  };
  'vaultbrain-client.ws-state-change': {
    from: 'idle' | 'connecting' | 'open' | 'closing' | 'closed';
    to: 'idle' | 'connecting' | 'open' | 'closing' | 'closed';
  };
  'toast.show': {
    id: string;
    variant: 'info' | 'success' | 'warning' | 'error';
    message: string;
  };
  'toast.dismiss': { id: string };
  'errorBoundary.caught': {
    moduleSlug: string;
    err: unknown;
  };
};

/**
 * The shared default bus instance. Every module is expected to import
 * this rather than create its own — that's what makes cross-lane
 * subscription possible (e.g. PolyCo.World subscribing to
 * `progression.event` regardless of which lane emitted it).
 *
 * Tests should create their own with `createEventBus<NjzEventMap>()`
 * for isolation.
 */
export const defaultEventBus: EventBus<NjzEventMap> = createEventBus<NjzEventMap>();
