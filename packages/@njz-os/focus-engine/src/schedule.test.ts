import { describe, expect, it } from 'vitest';
import {
  computeFocusScore,
  isDailyActive,
  isOneTimeActive,
  isScheduleActive,
  isWeeklyActive,
  type FocusSyncSchedule,
  type OneTimeSchedule,
  type RecurringDailySchedule,
  type RecurringWeeklySchedule,
} from './schedule';

const UTC = 'UTC';
const NYC = 'America/New_York';

function utcDate(s: string): Date {
  return new Date(s);
}

describe('isDailyActive', () => {
  const morningSchedule: RecurringDailySchedule = {
    id: 'morning',
    kind: 'recurring-daily',
    startsAt: '2026-05-30T09:00:00.000Z',
    durationMs: 3 * 60 * 60_000,
    startLocalTime: '09:00',
    durationMinutes: 180,
  };

  it('returns true inside the window', () => {
    expect(isDailyActive(morningSchedule, utcDate('2026-05-30T10:30:00.000Z'), UTC)).toBe(true);
  });

  it('returns false before the window', () => {
    expect(isDailyActive(morningSchedule, utcDate('2026-05-30T08:00:00.000Z'), UTC)).toBe(false);
  });

  it('returns false after the window', () => {
    expect(isDailyActive(morningSchedule, utcDate('2026-05-30T12:30:00.000Z'), UTC)).toBe(false);
  });

  const nightSchedule: RecurringDailySchedule = {
    id: 'sleep',
    kind: 'recurring-daily',
    startsAt: '2026-05-30T22:00:00.000Z',
    durationMs: 8 * 60 * 60_000,
    startLocalTime: '22:00',
    durationMinutes: 480,
  };

  it('cross-midnight: active at 23:00', () => {
    expect(isDailyActive(nightSchedule, utcDate('2026-05-30T23:00:00.000Z'), UTC)).toBe(true);
  });

  it('cross-midnight: active at 02:00 (next day)', () => {
    expect(isDailyActive(nightSchedule, utcDate('2026-05-31T02:00:00.000Z'), UTC)).toBe(true);
  });

  it('cross-midnight: inactive at 07:00 (after window)', () => {
    expect(isDailyActive(nightSchedule, utcDate('2026-05-31T07:00:00.000Z'), UTC)).toBe(false);
  });

  it('local-time-zone aware: NYC at 09:00 local = 13:00 UTC in summer', () => {
    expect(isDailyActive(morningSchedule, utcDate('2026-05-30T13:30:00.000Z'), NYC)).toBe(true);
  });
});

describe('isWeeklyActive', () => {
  const weekday: RecurringWeeklySchedule = {
    id: 'wd',
    kind: 'recurring-weekly',
    startsAt: '2026-05-30T09:00:00.000Z',
    durationMs: 3 * 60 * 60_000,
    startLocalTime: '09:00',
    durationMinutes: 180,
    weekdays: [1, 2, 3, 4, 5],
  };

  it('fires on a Monday (2026-06-01)', () => {
    expect(isWeeklyActive(weekday, utcDate('2026-06-01T10:00:00.000Z'), UTC)).toBe(true);
  });

  it('does not fire on a Saturday (2026-05-30)', () => {
    expect(isWeeklyActive(weekday, utcDate('2026-05-30T10:00:00.000Z'), UTC)).toBe(false);
  });

  it('cross-midnight on a Friday spills into Saturday morning', () => {
    const friNight: RecurringWeeklySchedule = {
      ...weekday,
      startLocalTime: '22:00',
      durationMinutes: 480,
      weekdays: [5],
    };
    expect(isWeeklyActive(friNight, utcDate('2026-06-06T02:00:00.000Z'), UTC)).toBe(true);
  });
});

describe('isOneTimeActive', () => {
  const oneTime: OneTimeSchedule = {
    id: 'meeting',
    kind: 'one-time',
    startsAt: '2026-05-30T14:00:00.000Z',
    durationMs: 60 * 60_000,
  };

  it('returns true during the window', () => {
    expect(isOneTimeActive(oneTime, utcDate('2026-05-30T14:30:00.000Z'))).toBe(true);
  });

  it('returns false outside the window', () => {
    expect(isOneTimeActive(oneTime, utcDate('2026-05-30T16:00:00.000Z'))).toBe(false);
  });
});

describe('isScheduleActive dispatch', () => {
  it('routes focus-sync to the active flag', () => {
    const focusSync: FocusSyncSchedule = {
      id: 'fs',
      kind: 'focus-sync',
      startsAt: 'n/a',
      durationMs: 0,
      active: true,
    };
    expect(isScheduleActive(focusSync, utcDate('2026-05-30T10:00:00.000Z'), UTC)).toBe(true);
    expect(isScheduleActive({ ...focusSync, active: false }, utcDate('2026-05-30T10:00:00.000Z'), UTC)).toBe(false);
  });
});

describe('computeFocusScore', () => {
  it('starts at 100 with no attempted blocks', () => {
    expect(computeFocusScore(0, 'moderate')).toBe(100);
  });

  it('penalises harder at higher enforcement levels', () => {
    expect(computeFocusScore(5, 'gentle')).toBeGreaterThan(
      computeFocusScore(5, 'maximum')
    );
  });

  it('clamps at 0', () => {
    expect(computeFocusScore(100, 'maximum')).toBe(0);
  });
});
