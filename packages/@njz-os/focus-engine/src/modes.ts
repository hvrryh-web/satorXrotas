/**
 * Lane A — Focus Engine mode definitions.
 *
 * Mirrors ADR-0009. Each mode has `workMs` (work phase) + `breakMs`
 * (break phase). The state machine loops through work → break →
 * work → break until the user completes or abandons.
 *
 * Naming convention: `<mode>_<work-minutes>_<break-minutes>`.
 */

export type SessionMode = 'pomodoro_25_5' | 'deep_work_50_10' | 'sprint_15_3' | 'flow_90_20';

export const MODE_DEFINITIONS: Record<
  SessionMode,
  { workMs: number; breakMs: number; label: string; description: string }
> = {
  pomodoro_25_5: {
    workMs: 25 * 60_000,
    breakMs: 5 * 60_000,
    label: 'Pomodoro 25 / 5',
    description: 'Classic 25-minute work block, 5-minute break.',
  },
  deep_work_50_10: {
    workMs: 50 * 60_000,
    breakMs: 10 * 60_000,
    label: 'Deep Work 50 / 10',
    description: '50 minutes of focus, 10-minute recovery.',
  },
  sprint_15_3: {
    workMs: 15 * 60_000,
    breakMs: 3 * 60_000,
    label: 'Sprint 15 / 3',
    description: 'Short bursts for momentum.',
  },
  flow_90_20: {
    workMs: 90 * 60_000,
    breakMs: 20 * 60_000,
    label: 'Flow 90 / 20',
    description: 'Long uninterrupted sessions for flow state.',
  },
};
