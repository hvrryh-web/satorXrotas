export type EnforcementLevel = 'gentle' | 'moderate' | 'strict' | 'maximum';

export interface BlockerSettings {
  enforcementLevel: EnforcementLevel;
  whitelist: string[];
  overrideCooldownSeconds: number;
  overrideLimitPerDay: number;
}

export interface BlockSchedule {
  id: string;
  kind: 'recurring-daily' | 'recurring-weekly' | 'one-time' | 'focus-sync' | 'smart';
  startsAt: string;
  durationMs: number;
}

export interface BlockAttempt {
  at: string;
  url: string;
  scheduleId: string;
  overridden: boolean;
}
