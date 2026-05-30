import type { ModuleSlug, ProgressionEvent, StreakState, XpTotals } from '@njz-os/core';

export * from './useProgression';
export * from './useOptimisticMutation';


export interface ProgressionState {
  xp: XpTotals;
  streaks: Record<ModuleSlug, StreakState>;
}

export function emptyXpTotals(): XpTotals {
  return {
    'focus-hero': 0,
    soundscapes: 0,
    'distraction-blocker': 0,
    'writing-space': 0,
    'micro-learning': 0,
    'brain-training': 0,
    'polyco-world': 0,
  };
}

export function applyEvent(state: ProgressionState, event: ProgressionEvent): ProgressionState {
  if (event.kind === 'session.complete') {
    return {
      ...state,
      xp: { ...state.xp, [event.module]: state.xp[event.module] + event.xpAwarded },
    };
  }
  if (event.kind === 'streak.extend') {
    const prev = state.streaks[event.module];
    return {
      ...state,
      streaks: {
        ...state.streaks,
        [event.module]: {
          currentDays: event.newCurrent,
          longestDays: Math.max(prev.longestDays, event.newCurrent),
          lastActiveAt: event.at,
        },
      },
    };
  }
  if (event.kind === 'streak.break') {
    return {
      ...state,
      streaks: {
        ...state.streaks,
        [event.module]: { ...state.streaks[event.module], currentDays: 0 },
      },
    };
  }
  return state;
}
