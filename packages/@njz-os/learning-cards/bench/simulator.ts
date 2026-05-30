/**
 * PRX-25-SPRINT-02 — Reference SRS simulators.
 *
 * Pure TypeScript implementations of SM-2 (canonical) and a stub
 * FSRS-5-lite for offline comparison. The bench (`runBench.ts`,
 * follow-up) wires these up against a synthetic cohort.
 */

export interface CardState {
  interval: number;
  easeFactor: number;
  repetitions: number;
}

export const SM2_INITIAL: CardState = {
  interval: 0,
  easeFactor: 2.5,
  repetitions: 0,
};

/**
 * Canonical SM-2: quality on 0-5 scale.
 *  - q < 3 → interval resets to 1 day; repetitions reset to 0.
 *  - q ≥ 3 → increment repetitions; advance interval.
 *  - ease factor decays on low quality, grows on high.
 */
export function sm2Update(state: CardState, quality: number): CardState {
  if (quality < 3) {
    return {
      ...state,
      repetitions: 0,
      interval: 1,
      easeFactor: Math.max(1.3, state.easeFactor - 0.2),
    };
  }
  const newRepetitions = state.repetitions + 1;
  let newInterval: number;
  if (newRepetitions === 1) newInterval = 1;
  else if (newRepetitions === 2) newInterval = 6;
  else newInterval = Math.round(state.interval * state.easeFactor);
  const newEf = Math.max(
    1.3,
    state.easeFactor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
  );
  return {
    repetitions: newRepetitions,
    interval: newInterval,
    easeFactor: newEf,
  };
}

/**
 * Interval-jitter variant: ± 10 % around SM-2's recommendation.
 * Reduces "everything due Monday" pile-ups for daily-streak users.
 */
export function sm2JitterUpdate(
  state: CardState,
  quality: number,
  rng: () => number = Math.random
): CardState {
  const next = sm2Update(state, quality);
  const jitter = 1 + (rng() * 0.2 - 0.1);
  return { ...next, interval: Math.max(1, Math.round(next.interval * jitter)) };
}

/**
 * FSRS-5-lite stub. Real FSRS-5 derives stability + difficulty +
 * retrievability via a parameter vector trained on millions of reviews
 * (Anki's open dataset). This stub gives a directionally similar curve
 * to enable the bench harness to compile without the full parameter
 * vector. Replace with full implementation before running the actual
 * bench.
 */
export interface FsrsState {
  stability: number;
  difficulty: number;
  reps: number;
}

export const FSRS_INITIAL: FsrsState = {
  stability: 1,
  difficulty: 5,
  reps: 0,
};

export function fsrsLiteUpdate(state: FsrsState, quality: number): FsrsState {
  const failed = quality < 3;
  const newDifficulty = Math.max(
    1,
    Math.min(10, state.difficulty + (failed ? 0.5 : -0.1))
  );
  const stabilityMultiplier = failed ? 0.2 : 1 + (quality - 3) * 0.5;
  const newStability = Math.max(0.5, state.stability * stabilityMultiplier);
  return {
    stability: newStability,
    difficulty: newDifficulty,
    reps: state.reps + 1,
  };
}

/**
 * Retention at `t` days for FSRS-style state — exponential decay
 * by stability.
 */
export function fsrsRetention(state: FsrsState, days: number): number {
  return Math.exp(-days / state.stability);
}
