import { describe, expect, it } from 'vitest';
import {
  buildCrossfadeSchedule,
  gainAtTime,
  totalGainAtTime,
} from './scheduler';

describe('buildCrossfadeSchedule', () => {
  it('returns one window per cycle', () => {
    const out = buildCrossfadeSchedule({
      loopSeconds: 300,
      crossfadeSeconds: 5,
      anchorSec: 0,
      cycles: 4,
      peakGain: 1,
    });
    expect(out).toHaveLength(4);
  });

  it('first window: full gain through fade-out, then ramp down', () => {
    const [w] = buildCrossfadeSchedule({
      loopSeconds: 10,
      crossfadeSeconds: 2,
      anchorSec: 0,
      cycles: 1,
      peakGain: 0.9,
    });
    expect(w!.startSec).toBe(0);
    expect(w!.keyframes).toEqual([
      { timeSec: 0, gain: 0.9 },
      { timeSec: 8, gain: 0.9 },
      { timeSec: 10, gain: 0 },
    ]);
  });

  it('subsequent windows: fade-in + peak hold + fade-out', () => {
    const windows = buildCrossfadeSchedule({
      loopSeconds: 10,
      crossfadeSeconds: 2,
      anchorSec: 0,
      cycles: 2,
      peakGain: 1,
    });
    const w1 = windows[1]!;
    expect(w1.startSec).toBe(8);
    expect(w1.keyframes[0]).toEqual({ timeSec: 8, gain: 0 });
    expect(w1.keyframes[1]).toEqual({ timeSec: 10, gain: 1 });
  });

  it('throws if crossfade ≥ loop', () => {
    expect(() =>
      buildCrossfadeSchedule({
        loopSeconds: 5,
        crossfadeSeconds: 5,
        anchorSec: 0,
        cycles: 2,
        peakGain: 1,
      })
    ).toThrow();
  });

  it('zero crossfade emits one keyframe per window', () => {
    const out = buildCrossfadeSchedule({
      loopSeconds: 10,
      crossfadeSeconds: 0,
      anchorSec: 0,
      cycles: 3,
      peakGain: 0.8,
    });
    expect(out).toHaveLength(3);
    expect(out[2]!.keyframes).toEqual([{ timeSec: 20, gain: 0.8 }]);
  });

  it('zero cycles returns empty', () => {
    expect(
      buildCrossfadeSchedule({
        loopSeconds: 10,
        crossfadeSeconds: 1,
        anchorSec: 0,
        cycles: 0,
        peakGain: 1,
      })
    ).toEqual([]);
  });
});

describe('gainAtTime + boundary continuity', () => {
  const windows = buildCrossfadeSchedule({
    loopSeconds: 10,
    crossfadeSeconds: 2,
    anchorSec: 0,
    cycles: 3,
    peakGain: 1,
  });

  it('linearly interpolates within a ramp segment', () => {
    const w1 = windows[1]!;
    expect(gainAtTime(w1, 9)).toBeCloseTo(0.5, 5);
  });

  it('boundary continuity: total gain ≈ peak across the crossfade', () => {
    for (let t = 8; t <= 10; t += 0.1) {
      const total = totalGainAtTime(windows, t);
      expect(total).toBeGreaterThan(0.99);
      expect(total).toBeLessThan(1.01);
    }
  });

  it('boundary continuity in overlap zones: total stays within ±0.5 dB of peak', () => {
    const overlaps = [
      [8, 10],
      [16, 18],
    ] as const;
    for (const [from, to] of overlaps) {
      for (let t = from; t <= to; t += 0.05) {
        const total = totalGainAtTime(windows, t);
        const dbFromPeak = Math.abs(20 * Math.log10(total));
        expect(dbFromPeak).toBeLessThan(0.5);
      }
    }
  });
});
