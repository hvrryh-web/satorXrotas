import { describe, expect, it } from 'vitest';
import {
  bandRange,
  DEFAULT_PRESETS,
  pairFrequencies,
  presetById,
  validatePreset,
} from './binaural';

describe('binaural presets', () => {
  it('all default presets fall inside their band range', () => {
    for (const preset of DEFAULT_PRESETS) {
      const [lo, hi] = bandRange[preset.band];
      expect(preset.beatHz).toBeGreaterThanOrEqual(lo);
      expect(preset.beatHz).toBeLessThanOrEqual(hi);
    }
  });

  it('presetById returns the matching preset or null', () => {
    expect(presetById('alpha-calm')?.band).toBe('alpha');
    expect(presetById('does-not-exist')).toBeNull();
  });
});

describe('pairFrequencies', () => {
  it('produces left + right symmetric around the carrier', () => {
    const { leftHz, rightHz } = pairFrequencies({
      id: 'x',
      band: 'alpha',
      carrierHz: 200,
      beatHz: 10,
      durationMs: 1000,
    });
    expect(leftHz).toBe(195);
    expect(rightHz).toBe(205);
    expect(rightHz - leftHz).toBe(10);
  });
});

describe('validatePreset', () => {
  it('accepts a valid candidate', () => {
    const res = validatePreset({
      id: 'custom-1',
      band: 'beta',
      carrierHz: 200,
      beatHz: 20,
    });
    expect(res.ok).toBe(true);
  });

  it('rejects missing id', () => {
    expect(validatePreset({ band: 'beta', carrierHz: 200, beatHz: 20 })).toMatchObject({
      ok: false,
    });
  });

  it('rejects carrier outside 50..800 Hz', () => {
    expect(validatePreset({ id: 'x', band: 'alpha', carrierHz: 10, beatHz: 10 })).toMatchObject({
      ok: false,
    });
    expect(validatePreset({ id: 'x', band: 'alpha', carrierHz: 900, beatHz: 10 })).toMatchObject({
      ok: false,
    });
  });

  it('rejects beat outside the chosen band', () => {
    expect(
      validatePreset({ id: 'x', band: 'alpha', carrierHz: 200, beatHz: 50 })
    ).toMatchObject({ ok: false });
  });

  it('defaults durationMs to 30 minutes if omitted', () => {
    const res = validatePreset({ id: 'x', band: 'alpha', carrierHz: 200, beatHz: 10 });
    if (res.ok) expect(res.preset.durationMs).toBe(30 * 60_000);
    else throw new Error('expected ok');
  });
});
