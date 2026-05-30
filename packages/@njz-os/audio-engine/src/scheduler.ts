/**
 * Lane B Task B3 — Gapless crossfade scheduler.
 *
 * Per stem we schedule two AudioBufferSourceNodes on a recurring cycle:
 *   - source A starts at t0, runs for loopSeconds + crossfade
 *   - source B starts at t0 + loopSeconds - crossfade,
 *                 runs for loopSeconds + crossfade
 *   - A fades out linearly over [t0 + loopSeconds - crossfade,
 *                                t0 + loopSeconds]
 *   - B fades in over the same window
 *
 * The pure scheduler computes the gain-ramp keyframes for a given
 * window; the AudioContext-bound consumer in graph.ts applies them via
 * `linearRampToValueAtTime`.
 *
 * Designed for OfflineAudioContext testing: callers can render a small
 * window with two short stems and assert the gain at the loop boundary
 * stays within ±0.5 dB of the sum (no audible jump). See
 * scheduler.test.ts.
 */

export interface CrossfadeKeyframe {
  /** Absolute time on the audio timeline, seconds. */
  timeSec: number;
  /** Gain at that time, 0..1. */
  gain: number;
}

export interface CrossfadeWindow {
  /** When this source's `start(when)` is scheduled. */
  startSec: number;
  /** Duration this source plays before being stopped (or until next ramp ends). */
  durationSec: number;
  /** Linear ramp keyframes applied to this source's gain node. */
  keyframes: CrossfadeKeyframe[];
}

export interface SchedulerInput {
  /** Loop length of the stem in seconds (matches manifest.loopSeconds). */
  loopSeconds: number;
  /** Crossfade overlap in seconds (matches manifest.crossfadeSeconds). */
  crossfadeSeconds: number;
  /** Anchor time on the audio timeline where the first loop starts. */
  anchorSec: number;
  /** How many full loop cycles to plan. */
  cycles: number;
  /** Default peak gain for the stem (after the fade ramp), 0..1. */
  peakGain: number;
}

export function buildCrossfadeSchedule(input: SchedulerInput): CrossfadeWindow[] {
  if (input.cycles <= 0) return [];
  if (input.crossfadeSeconds <= 0) {
    return Array.from({ length: input.cycles }, (_, i) => ({
      startSec: input.anchorSec + i * input.loopSeconds,
      durationSec: input.loopSeconds,
      keyframes: [
        { timeSec: input.anchorSec + i * input.loopSeconds, gain: input.peakGain },
      ],
    }));
  }
  if (input.crossfadeSeconds >= input.loopSeconds) {
    throw new Error(
      `crossfade (${input.crossfadeSeconds}s) must be < loop length (${input.loopSeconds}s)`
    );
  }

  const windows: CrossfadeWindow[] = [];
  for (let i = 0; i < input.cycles; i += 1) {
    // Each cycle overlaps with the next by `crossfadeSeconds`.
    const startSec = input.anchorSec + i * (input.loopSeconds - input.crossfadeSeconds);
    const fadeOutStart = startSec + input.loopSeconds - input.crossfadeSeconds;
    const fadeOutEnd = startSec + input.loopSeconds;
    windows.push({
      startSec,
      durationSec: input.loopSeconds,
      keyframes:
        i === 0
          ? [
              { timeSec: startSec, gain: input.peakGain },
              { timeSec: fadeOutStart, gain: input.peakGain },
              { timeSec: fadeOutEnd, gain: 0 },
            ]
          : [
              { timeSec: startSec, gain: 0 },
              { timeSec: startSec + input.crossfadeSeconds, gain: input.peakGain },
              { timeSec: fadeOutStart, gain: input.peakGain },
              { timeSec: fadeOutEnd, gain: 0 },
            ],
    });
  }
  return windows;
}

/**
 * Linear-interpolated gain at `tSec` for a CrossfadeWindow. Pure,
 * tested function so the AudioContext-bound consumer can be smoke-tested
 * even without an audio runtime.
 */
export function gainAtTime(window: CrossfadeWindow, tSec: number): number {
  const kfs = window.keyframes;
  if (kfs.length === 0) return 0;
  if (tSec <= kfs[0]!.timeSec) return kfs[0]!.gain;
  if (tSec >= kfs[kfs.length - 1]!.timeSec) return kfs[kfs.length - 1]!.gain;
  for (let i = 1; i < kfs.length; i += 1) {
    const a = kfs[i - 1]!;
    const b = kfs[i]!;
    if (tSec >= a.timeSec && tSec <= b.timeSec) {
      const span = b.timeSec - a.timeSec;
      if (span <= 0) return b.gain;
      const t = (tSec - a.timeSec) / span;
      return a.gain + (b.gain - a.gain) * t;
    }
  }
  return 0;
}

/**
 * Sum the active sources' gain at `tSec`. Used by the loop-boundary
 * waveform test in scheduler.test.ts to verify no >0.5 dB jump:
 *   total = sum(gainAtTime(window_i, t))  should stay within
 *   peakGain * [10^(-0.5/20), 10^(+0.5/20)] across the boundary.
 */
export function totalGainAtTime(
  windows: CrossfadeWindow[],
  tSec: number
): number {
  return windows.reduce((acc, w) => {
    if (tSec < w.startSec) return acc;
    if (tSec > w.startSec + w.durationSec) return acc;
    return acc + gainAtTime(w, tSec);
  }, 0);
}
