import type { SessionId, UserId } from '@njz-os/core';

export type SessionMode = 'pomodoro_25_5' | 'deep_work_50_10' | 'sprint_15_3' | 'flow_90_20';

export interface FocusSession {
  id: SessionId;
  userId: UserId;
  mode: SessionMode;
  startedAt: string;
  durationMs: number;
  state: 'pending' | 'running' | 'paused' | 'completed' | 'abandoned';
}
