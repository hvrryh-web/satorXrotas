import { beforeAll, describe, expect, it } from 'vitest';
import {
  focusReducer,
  initialContext,
  msRemaining,
  secondsRemaining,
  progressFraction,
  isPhaseElapsed,
  type FocusContext,
} from './machine';

const T0 = 1_000_000_000_000;
const MIN = 60_000;

describe('focusReducer', () => {
  it('initialContext starts pending in work phase at default mode', () => {
    const ctx = initialContext();
    expect(ctx.status).toBe('pending');
    expect(ctx.phase).toBe('work');
    expect(ctx.mode).toBe('pomodoro_25_5');
    expect(ctx.startedAtMs).toBeNull();
  });

  it('START transitions pending → running and stamps startedAtMs', () => {
    const ctx = focusReducer(initialContext(), {
      kind: 'START',
      mode: 'deep_work_50_10',
      nowMs: T0,
    });
    expect(ctx.status).toBe('running');
    expect(ctx.mode).toBe('deep_work_50_10');
    expect(ctx.startedAtMs).toBe(T0);
  });

  it('START is a no-op if already running', () => {
    let ctx = focusReducer(initialContext(), {
      kind: 'START',
      mode: 'pomodoro_25_5',
      nowMs: T0,
    });
    ctx = focusReducer(ctx, { kind: 'START', mode: 'flow_90_20', nowMs: T0 + 60_000 });
    expect(ctx.mode).toBe('pomodoro_25_5');
    expect(ctx.startedAtMs).toBe(T0);
  });

  it('PAUSE → RESUME accumulates pausedMs', () => {
    let ctx = focusReducer(initialContext(), {
      kind: 'START',
      mode: 'pomodoro_25_5',
      nowMs: T0,
    });
    ctx = focusReducer(ctx, { kind: 'PAUSE', nowMs: T0 + 5 * MIN });
    expect(ctx.status).toBe('paused');
    expect(ctx.pauseStartedAtMs).toBe(T0 + 5 * MIN);
    ctx = focusReducer(ctx, { kind: 'RESUME', nowMs: T0 + 8 * MIN });
    expect(ctx.status).toBe('running');
    expect(ctx.pausedMs).toBe(3 * MIN);
    expect(ctx.pauseStartedAtMs).toBeNull();
  });

  it('PAUSE while paused is a no-op', () => {
    let ctx = focusReducer(initialContext(), {
      kind: 'START',
      mode: 'pomodoro_25_5',
      nowMs: T0,
    });
    ctx = focusReducer(ctx, { kind: 'PAUSE', nowMs: T0 + 5 * MIN });
    const before = ctx;
    ctx = focusReducer(ctx, { kind: 'PAUSE', nowMs: T0 + 7 * MIN });
    expect(ctx).toBe(before);
  });

  it('NEXT_PHASE alternates work ↔ break and counts completions', () => {
    let ctx = focusReducer(initialContext(), {
      kind: 'START',
      mode: 'pomodoro_25_5',
      nowMs: T0,
    });
    ctx = focusReducer(ctx, { kind: 'NEXT_PHASE', nowMs: T0 + 25 * MIN });
    expect(ctx.phase).toBe('break');
    expect(ctx.completedWorkPhases).toBe(1);
    ctx = focusReducer(ctx, { kind: 'NEXT_PHASE', nowMs: T0 + 30 * MIN });
    expect(ctx.phase).toBe('work');
    expect(ctx.completedBreakPhases).toBe(1);
  });

  it('COMPLETE locks status; ABANDON does the same', () => {
    let ctx = focusReducer(initialContext(), {
      kind: 'START',
      mode: 'pomodoro_25_5',
      nowMs: T0,
    });
    ctx = focusReducer(ctx, { kind: 'COMPLETE', nowMs: T0 + 25 * MIN });
    expect(ctx.status).toBe('completed');
    ctx = focusReducer(ctx, { kind: 'PAUSE', nowMs: T0 + 26 * MIN });
    expect(ctx.status).toBe('completed');
  });

  it('ABANDON is terminal', () => {
    let ctx = focusReducer(initialContext(), {
      kind: 'START',
      mode: 'pomodoro_25_5',
      nowMs: T0,
    });
    ctx = focusReducer(ctx, { kind: 'ABANDON', nowMs: T0 + 5 * MIN });
    expect(ctx.status).toBe('abandoned');
  });
});

describe('selectors', () => {
  let startedCtx: FocusContext;
  beforeAll(() => {
    startedCtx = focusReducer(initialContext(), {
      kind: 'START',
      mode: 'pomodoro_25_5',
      nowMs: T0,
    });
  });

  it('msRemaining: full duration at start', () => {
    expect(msRemaining(startedCtx, T0)).toBe(25 * MIN);
  });

  it('msRemaining: linear decrement with elapsed time', () => {
    expect(msRemaining(startedCtx, T0 + 10 * MIN)).toBe(15 * MIN);
  });

  it('msRemaining: clamps at 0', () => {
    expect(msRemaining(startedCtx, T0 + 26 * MIN)).toBe(0);
  });

  it('msRemaining: pause freezes the timer', () => {
    let ctx = focusReducer(startedCtx, { kind: 'PAUSE', nowMs: T0 + 10 * MIN });
    expect(msRemaining(ctx, T0 + 14 * MIN)).toBe(15 * MIN);
    ctx = focusReducer(ctx, { kind: 'RESUME', nowMs: T0 + 14 * MIN });
    expect(msRemaining(ctx, T0 + 16 * MIN)).toBe(13 * MIN);
  });

  it('msRemaining: zero for completed/abandoned', () => {
    const completed = focusReducer(startedCtx, {
      kind: 'COMPLETE',
      nowMs: T0 + 10 * MIN,
    });
    expect(msRemaining(completed, T0 + 100 * MIN)).toBe(0);
  });

  it('secondsRemaining: ms rounded up', () => {
    expect(secondsRemaining(startedCtx, T0 + 24 * MIN + 30_000)).toBe(30);
  });

  it('progressFraction: 0 at start, ~1 at end', () => {
    expect(progressFraction(startedCtx, T0)).toBe(0);
    expect(progressFraction(startedCtx, T0 + 12.5 * MIN)).toBeCloseTo(0.5, 2);
    expect(progressFraction(startedCtx, T0 + 25 * MIN)).toBe(1);
  });

  it('isPhaseElapsed: true once timer hits zero', () => {
    expect(isPhaseElapsed(startedCtx, T0 + 10 * MIN)).toBe(false);
    expect(isPhaseElapsed(startedCtx, T0 + 25 * MIN)).toBe(true);
  });

  it('phase transition resets remaining to next phase duration', () => {
    let ctx = focusReducer(startedCtx, { kind: 'NEXT_PHASE', nowMs: T0 + 25 * MIN });
    expect(ctx.phase).toBe('break');
    expect(msRemaining(ctx, T0 + 25 * MIN)).toBe(5 * MIN);
    ctx = focusReducer(ctx, { kind: 'NEXT_PHASE', nowMs: T0 + 30 * MIN });
    expect(ctx.phase).toBe('work');
    expect(msRemaining(ctx, T0 + 30 * MIN)).toBe(25 * MIN);
  });
});
