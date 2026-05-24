import type { UserId, SessionId } from './identity';

export type ModuleSlug =
  | 'focus-hero'
  | 'soundscapes'
  | 'distraction-blocker'
  | 'writing-space'
  | 'micro-learning'
  | 'brain-training'
  | 'polyco-world';

export interface StreakState {
  currentDays: number;
  longestDays: number;
  lastActiveAt: string;
}

export type XpTotals = Record<ModuleSlug, number>;

export type ProgressionEvent =
  | { kind: 'session.start'; userId: UserId; sessionId: SessionId; module: ModuleSlug; at: string }
  | {
      kind: 'session.complete';
      userId: UserId;
      sessionId: SessionId;
      module: ModuleSlug;
      durationMs: number;
      xpAwarded: number;
      at: string;
    }
  | {
      kind: 'session.abandon';
      userId: UserId;
      sessionId: SessionId;
      module: ModuleSlug;
      at: string;
    }
  | { kind: 'streak.extend'; userId: UserId; module: ModuleSlug; newCurrent: number; at: string }
  | { kind: 'streak.break'; userId: UserId; module: ModuleSlug; at: string };

export interface Reward {
  id: string;
  kind: 'decoration' | 'currency' | 'aura' | 'title';
  module: ModuleSlug;
  unlockedBy: string;
}
