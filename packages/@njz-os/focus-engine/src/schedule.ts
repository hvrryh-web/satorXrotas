/**
 * Lane D Task D1 — Block schedule resolver.
 *
 * Pure functions that decide whether a `BlockSchedule` is active at a
 * given instant. Schedules come in four shapes per the EXPANDED.md:
 *
 *   - recurring-daily   — fires every day at startsAt's local time
 *   - recurring-weekly  — fires on the configured weekdays
 *   - one-time          — fires once at startsAt
 *   - focus-sync        — armed for the duration of an active FocusSession
 *
 * Handles DST shifts and cross-midnight schedules. Time zones use the
 * user's IANA tz string from vaultbrain; for purity the resolver takes
 * the tz as a parameter rather than reading it from globals.
 */

import type { BlockSchedule, EnforcementLevel } from './blocker';

export interface RecurringDailySchedule extends BlockSchedule {
  kind: 'recurring-daily';
  /** "HH:mm" local time. */
  startLocalTime: string;
  /** Window length in minutes; can cross midnight (e.g. 22:00 + 480 min → 06:00). */
  durationMinutes: number;
}

export interface RecurringWeeklySchedule extends BlockSchedule {
  kind: 'recurring-weekly';
  startLocalTime: string;
  durationMinutes: number;
  /** 0 = Sunday … 6 = Saturday. */
  weekdays: readonly number[];
}

export interface OneTimeSchedule extends BlockSchedule {
  kind: 'one-time';
  /** ISO 8601 instant. */
  startsAt: string;
  durationMs: number;
}

export interface FocusSyncSchedule extends BlockSchedule {
  kind: 'focus-sync';
  /** Whether a focus session is currently running (consumer toggles this). */
  active: boolean;
}

export type AnyBlockSchedule =
  | RecurringDailySchedule
  | RecurringWeeklySchedule
  | OneTimeSchedule
  | FocusSyncSchedule;

interface LocalParts {
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
  weekday: number;
}

function dateInZone(date: Date, timeZone: string): LocalParts {
  const dtf = new Intl.DateTimeFormat('en-US', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    weekday: 'short',
    hour12: false,
  });
  const parts = dtf.formatToParts(date);
  const get = (type: string): string => parts.find((p) => p.type === type)?.value ?? '0';
  const weekdayMap: Record<string, number> = {
    Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6,
  };
  return {
    year: Number(get('year')),
    month: Number(get('month')),
    day: Number(get('day')),
    hour: Number(get('hour') === '24' ? '0' : get('hour')),
    minute: Number(get('minute')),
    weekday: weekdayMap[get('weekday')] ?? 0,
  };
}

function parseHHMM(s: string): { hour: number; minute: number } {
  const [h, m] = s.split(':').map(Number);
  return { hour: h ?? 0, minute: m ?? 0 };
}

/**
 * Returns true when `now` falls inside the recurring-daily window in
 * the user's local time. Handles cross-midnight windows by checking
 * both "today's start + duration" and "yesterday's start + duration".
 */
export function isDailyActive(
  schedule: RecurringDailySchedule,
  now: Date,
  timeZone: string
): boolean {
  const local = dateInZone(now, timeZone);
  const start = parseHHMM(schedule.startLocalTime);
  const startMinOfDay = start.hour * 60 + start.minute;
  const endMinOfDay = startMinOfDay + schedule.durationMinutes;
  const nowMinOfDay = local.hour * 60 + local.minute;

  if (endMinOfDay <= 24 * 60) {
    return nowMinOfDay >= startMinOfDay && nowMinOfDay < endMinOfDay;
  }
  // Cross-midnight: window spans today's start..24:00 and tomorrow's 0:00..(end-24:00).
  const wrappedEnd = endMinOfDay - 24 * 60;
  if (nowMinOfDay >= startMinOfDay) return true;
  return nowMinOfDay < wrappedEnd;
}

export function isWeeklyActive(
  schedule: RecurringWeeklySchedule,
  now: Date,
  timeZone: string
): boolean {
  const local = dateInZone(now, timeZone);
  const dailyView: RecurringDailySchedule = {
    ...(schedule as unknown as RecurringDailySchedule),
    kind: 'recurring-daily',
  };
  if (!schedule.weekdays.includes(local.weekday)) {
    // If the daily window already started "yesterday" and we are within the
    // wrapped portion, consider yesterday's weekday.
    const yesterday = (local.weekday + 6) % 7;
    if (!schedule.weekdays.includes(yesterday)) return false;
    const start = parseHHMM(schedule.startLocalTime);
    const startMinOfDay = start.hour * 60 + start.minute;
    const endMinOfDay = startMinOfDay + schedule.durationMinutes;
    if (endMinOfDay <= 24 * 60) return false;
    const wrappedEnd = endMinOfDay - 24 * 60;
    const nowMinOfDay = local.hour * 60 + local.minute;
    return nowMinOfDay < wrappedEnd;
  }
  return isDailyActive(dailyView, now, timeZone);
}

export function isOneTimeActive(schedule: OneTimeSchedule, now: Date): boolean {
  const startMs = new Date(schedule.startsAt).getTime();
  const nowMs = now.getTime();
  return nowMs >= startMs && nowMs < startMs + schedule.durationMs;
}

export function isFocusSyncActive(schedule: FocusSyncSchedule): boolean {
  return schedule.active;
}

export function isScheduleActive(
  schedule: AnyBlockSchedule,
  now: Date,
  timeZone: string
): boolean {
  switch (schedule.kind) {
    case 'recurring-daily':
      return isDailyActive(schedule, now, timeZone);
    case 'recurring-weekly':
      return isWeeklyActive(schedule, now, timeZone);
    case 'one-time':
      return isOneTimeActive(schedule, now);
    case 'focus-sync':
      return isFocusSyncActive(schedule);
    default: {
      const _exhaustive: never = schedule;
      return _exhaustive;
    }
  }
}

/**
 * Compute the Focus Score for a session per PS-003 §3.3.6.
 *
 * Heuristic: starts at 100, subtract 5 per attempted distraction (capped
 * by enforcement-level weighting). Strict / Maximum penalise harder.
 */
export function computeFocusScore(
  attemptedBlocks: number,
  enforcement: EnforcementLevel
): number {
  const weight: Record<EnforcementLevel, number> = {
    gentle: 2,
    moderate: 4,
    strict: 6,
    maximum: 10,
  };
  const raw = 100 - attemptedBlocks * weight[enforcement];
  return Math.max(0, Math.min(100, raw));
}
