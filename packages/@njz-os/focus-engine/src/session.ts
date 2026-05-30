/**
 * Lane A — FocusSession persistence payload (mirrors vaultbrain row).
 * The SessionMode type lives in ./modes.ts; this file re-exports it for
 * back-compat with Phase-0 consumers and adds the persisted-shape type.
 */

import type { SessionId, UserId } from '@njz-os/core';
import type { SessionMode } from './modes';

export type { SessionMode } from './modes';

export interface FocusSession {
  id: SessionId;
  userId: UserId;
  mode: SessionMode;
  startedAt: string;
  durationMs: number;
  state: 'pending' | 'running' | 'paused' | 'completed' | 'abandoned';
}
