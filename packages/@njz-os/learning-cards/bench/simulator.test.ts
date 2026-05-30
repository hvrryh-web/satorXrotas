import { describe, expect, it } from 'vitest';
import {
  SM2_INITIAL,
  sm2Update,
  sm2JitterUpdate,
  FSRS_INITIAL,
  fsrsLiteUpdate,
  fsrsRetention,
} from './simulator';

describe('SM-2 reference simulator', () => {
  it('quality < 3 resets repetitions and shrinks ease factor', () => {
    const next = sm2Update({ ...SM2_INITIAL, repetitions: 3, interval: 14 }, 1);
    expect(next.repetitions).toBe(0);
    expect(next.interval).toBe(1);
    expect(next.easeFactor).toBeLessThan(SM2_INITIAL.easeFactor);
    expect(next.easeFactor).toBeGreaterThanOrEqual(1.3);
  });

  it('quality ≥ 3 advances the interval canonically', () => {
    const s1 = sm2Update(SM2_INITIAL, 5);
    expect(s1.repetitions).toBe(1);
    expect(s1.interval).toBe(1);
    const s2 = sm2Update(s1, 5);
    expect(s2.repetitions).toBe(2);
    expect(s2.interval).toBe(6);
    const s3 = sm2Update(s2, 5);
    expect(s3.repetitions).toBe(3);
    expect(s3.interval).toBeGreaterThan(s2.interval);
  });

  it('ease factor is floored at 1.3', () => {
    let s = { ...SM2_INITIAL, easeFactor: 1.4 };
    for (let i = 0; i < 5; i += 1) s = sm2Update(s, 0);
    expect(s.easeFactor).toBe(1.3);
  });

  it('SM-2 + jitter stays within ± 10 % of canonical interval', () => {
    const baseState = { ...SM2_INITIAL, repetitions: 5, interval: 30, easeFactor: 2.5 };
    const baseline = sm2Update(baseState, 5).interval;
    for (let i = 0; i < 50; i += 1) {
      const jittered = sm2JitterUpdate(baseState, 5).interval;
      expect(jittered).toBeGreaterThanOrEqual(Math.floor(baseline * 0.9));
      expect(jittered).toBeLessThanOrEqual(Math.ceil(baseline * 1.1));
    }
  });
});

describe('FSRS-lite stub', () => {
  it('failed reviews collapse stability and bump difficulty', () => {
    const next = fsrsLiteUpdate(FSRS_INITIAL, 1);
    expect(next.stability).toBeLessThan(FSRS_INITIAL.stability);
    expect(next.difficulty).toBeGreaterThan(FSRS_INITIAL.difficulty);
  });

  it('successful reviews grow stability', () => {
    const next = fsrsLiteUpdate(FSRS_INITIAL, 5);
    expect(next.stability).toBeGreaterThan(FSRS_INITIAL.stability);
  });

  it('retention decays exponentially in days', () => {
    const r0 = fsrsRetention({ ...FSRS_INITIAL, stability: 10 }, 0);
    const r10 = fsrsRetention({ ...FSRS_INITIAL, stability: 10 }, 10);
    const r20 = fsrsRetention({ ...FSRS_INITIAL, stability: 10 }, 20);
    expect(r0).toBe(1);
    expect(r10).toBeLessThan(r0);
    expect(r20).toBeLessThan(r10);
  });
});
