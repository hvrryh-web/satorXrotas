/**
 * Lane A (Tasks A1 + A2) — Focus Engine state machine.
 *
 * Implements ADR-0009 exactly:
 *   pending → running.work → running.break → running.work → … →
 *     (COMPLETE → completed) | (ABANDON → abandoned) | (PAUSE → paused)
 *
 * Time is timestamp-based: the machine stores `startedAt` and accumulated
 * `pausedMs`. The selector `secondsRemaining()` re-derives time from
 * `Date.now()` so device sleeps, tab backgrounding, and cross-device
 * handoffs don't drift. Persistence happens at session boundaries
 * (start / complete / abandon) only — never per-tick — per ADR-0009.
 *
 * Pure reducer + selectors. No XState dependency: the lane spec
 * (EXPANDED.md §4 Task A1) suggested XState v5, but a hand-rolled
 * machine of this size is testable, dependency-free, and trivially
 * portable to XState later if observability needs grow. The reducer
 * pattern keeps the contract identical.
 */

import { MODE_DEFINITIONS, type SessionMode } from './modes';

export type FocusPhase = 'work' | 'break';

export type FocusStatus =
  | 'pending'
  | 'running'
  | 'paused'
  | 'completed'
  | 'abandoned';

export interface FocusContext {
  status: FocusStatus;
  mode: SessionMode;
  phase: FocusPhase;
  /** Wall-clock when the session started (ms since epoch) or null while pending. */
  startedAtMs: number | null;
  /** Total accumulated paused time across all pause events. */
  pausedMs: number;
  /** When the last `PAUSE` fired and we haven't resumed yet. */
  pauseStartedAtMs: number | null;
  /** Completed work phases this session (drives next phase). */
  completedWorkPhases: number;
  /** Completed break phases this session. */
  completedBreakPhases: number;
}

export type FocusEvent =
  | { kind: 'START'; mode: SessionMode; nowMs?: number }
  | { kind: 'PAUSE'; nowMs?: number }
  | { kind: 'RESUME'; nowMs?: number }
  | { kind: 'NEXT_PHASE'; nowMs?: number }
  | { kind: 'COMPLETE'; nowMs?: number }
  | { kind: 'ABANDON'; nowMs?: number };

export function initialContext(mode: SessionMode = 'pomodoro_25_5'): FocusContext {
  return {
    status: 'pending',
    mode,
    phase: 'work',
    startedAtMs: null,
    pausedMs: 0,
    pauseStartedAtMs: null,
    completedWorkPhases: 0,
    completedBreakPhases: 0,
  };
}

export function focusReducer(ctx: FocusContext, event: FocusEvent): FocusContext {
  const now = event.nowMs ?? Date.now();
  switch (event.kind) {
    case 'START': {
      if (ctx.status === 'running' || ctx.status === 'paused') return ctx;
      return {
        ...initialContext(event.mode),
        status: 'running',
        startedAtMs: now,
      };
    }
    case 'PAUSE': {
      if (ctx.status !== 'running') return ctx;
      return { ...ctx, status: 'paused', pauseStartedAtMs: now };
    }
    case 'RESUME': {
      if (ctx.status !== 'paused' || ctx.pauseStartedAtMs == null) return ctx;
      return {
        ...ctx,
        status: 'running',
        pausedMs: ctx.pausedMs + (now - ctx.pauseStartedAtMs),
        pauseStartedAtMs: null,
      };
    }
    case 'NEXT_PHASE': {
      if (ctx.status !== 'running') return ctx;
      if (ctx.phase === 'work') {
        return {
          ...ctx,
          phase: 'break',
          completedWorkPhases: ctx.completedWorkPhases + 1,
        };
      }
      return {
        ...ctx,
        phase: 'work',
        completedBreakPhases: ctx.completedBreakPhases + 1,
      };
    }
    case 'COMPLETE': {
      if (ctx.status === 'completed' || ctx.status === 'abandoned') return ctx;
      return { ...ctx, status: 'completed' };
    }
    case 'ABANDON': {
      if (ctx.status === 'completed' || ctx.status === 'abandoned') return ctx;
      return { ...ctx, status: 'abandoned' };
    }
    default:
      return ctx;
  }
}

/** ms remaining in the current phase, with drift correction. */
export function msRemaining(ctx: FocusContext, nowMs: number = Date.now()): number {
  if (ctx.startedAtMs == null) return phaseDurationMs(ctx);
  if (ctx.status === 'completed' || ctx.status === 'abandoned') return 0;
  const phaseStart = phaseStartMs(ctx);
  const liveNow =
    ctx.status === 'paused' && ctx.pauseStartedAtMs != null
      ? ctx.pauseStartedAtMs
      : nowMs;
  const elapsed = liveNow - phaseStart - ctx.pausedMs;
  const remaining = phaseDurationMs(ctx) - elapsed;
  return Math.max(0, remaining);
}

export function secondsRemaining(ctx: FocusContext, nowMs: number = Date.now()): number {
  return Math.ceil(msRemaining(ctx, nowMs) / 1_000);
}

/** Fraction of the current phase complete: 0..1. */
export function progressFraction(
  ctx: FocusContext,
  nowMs: number = Date.now()
): number {
  const total = phaseDurationMs(ctx);
  if (total === 0) return 1;
  return 1 - msRemaining(ctx, nowMs) / total;
}

/** True when the current phase's timer has reached zero. */
export function isPhaseElapsed(
  ctx: FocusContext,
  nowMs: number = Date.now()
): boolean {
  return msRemaining(ctx, nowMs) <= 0;
}

function phaseDurationMs(ctx: FocusContext): number {
  const def = MODE_DEFINITIONS[ctx.mode];
  return ctx.phase === 'work' ? def.workMs : def.breakMs;
}

function phaseStartMs(ctx: FocusContext): number {
  const start = ctx.startedAtMs ?? 0;
  const def = MODE_DEFINITIONS[ctx.mode];
  let offset = 0;
  for (let i = 0; i < ctx.completedWorkPhases; i += 1) offset += def.workMs;
  for (let i = 0; i < ctx.completedBreakPhases; i += 1) offset += def.breakMs;
  return start + offset;
}
