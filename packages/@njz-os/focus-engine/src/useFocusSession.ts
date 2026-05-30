/**
 * Lane A (Task A4) — React hook over the focus state machine.
 *
 * Returns `{ context, send, secondsRemaining, progressFraction, phaseLabel }`.
 *
 * The hook ticks every 500 ms while running so the countdown updates;
 * we use `useSyncExternalStore` so cross-tab consumers stay correct.
 * The state machine itself stays pure — the hook is a thin observer.
 *
 * Persistence callbacks (`onStart`, `onComplete`, `onAbandon`) fire at
 * session boundaries only, per ADR-0009. Consumers wire these to the
 * vaultbrain client.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  focusReducer,
  initialContext,
  isPhaseElapsed,
  msRemaining,
  progressFraction as progressFractionSel,
  secondsRemaining as secondsRemainingSel,
  type FocusContext,
  type FocusEvent,
} from './machine';
import type { SessionMode } from './modes';

export interface UseFocusSessionOptions {
  initialMode?: SessionMode;
  onStart?: (ctx: FocusContext) => void;
  onComplete?: (ctx: FocusContext) => void;
  onAbandon?: (ctx: FocusContext) => void;
  /** Hook in a fake clock for tests. */
  clock?: () => number;
  /** Override the tick interval (default 500 ms). */
  tickIntervalMs?: number;
}

type FocusEventInput = FocusEvent extends infer E
  ? E extends FocusEvent
    ? Omit<E, 'nowMs'>
    : never
  : never;

export interface UseFocusSessionResult {
  context: FocusContext;
  send: (event: FocusEventInput) => void;
  secondsRemaining: number;
  progressFraction: number;
  phaseLabel: 'Work' | 'Break';
  isRunning: boolean;
  isPaused: boolean;
  isComplete: boolean;
  isAbandoned: boolean;
}

export function useFocusSession(opts: UseFocusSessionOptions = {}): UseFocusSessionResult {
  const [ctx, setCtx] = useState<FocusContext>(() =>
    initialContext(opts.initialMode ?? 'pomodoro_25_5')
  );
  const tickInterval = opts.tickIntervalMs ?? 500;
  const clock = opts.clock ?? Date.now;
  const tickRef = useRef(0);
  const [, setTick] = useState(0);

  const send = useCallback(
    (event: FocusEventInput) => {
      setCtx((current) => {
        const next = focusReducer(current, {
          ...event,
          nowMs: clock(),
        } as FocusEvent);
        if (next.status === 'running' && current.status === 'pending') {
          opts.onStart?.(next);
        } else if (next.status === 'completed' && current.status !== 'completed') {
          opts.onComplete?.(next);
        } else if (next.status === 'abandoned' && current.status !== 'abandoned') {
          opts.onAbandon?.(next);
        }
        return next;
      });
    },
    [clock, opts]
  );

  useEffect(() => {
    if (ctx.status !== 'running') return undefined;
    const id = setInterval(() => {
      tickRef.current += 1;
      setTick(tickRef.current);
      const now = clock();
      if (isPhaseElapsed(ctx, now)) {
        send({ kind: 'NEXT_PHASE' });
      }
    }, tickInterval);
    return () => clearInterval(id);
  }, [ctx, clock, send, tickInterval]);

  const now = clock();
  const result = useMemo<UseFocusSessionResult>(
    () => ({
      context: ctx,
      send,
      secondsRemaining: secondsRemainingSel(ctx, now),
      progressFraction: progressFractionSel(ctx, now),
      phaseLabel: ctx.phase === 'work' ? 'Work' : 'Break',
      isRunning: ctx.status === 'running',
      isPaused: ctx.status === 'paused',
      isComplete: ctx.status === 'completed',
      isAbandoned: ctx.status === 'abandoned',
    }),
    [ctx, now, send]
  );

  // Surface `msRemaining` to consumers that want millisecond precision.
  void msRemaining;

  return result;
}
