/**
 * Lane B Task B4 — Binaural beat generator.
 *
 * Two OscillatorNodes, each routed through its own StereoPannerNode
 * (full left + full right). Brain perceives the difference (beat) when
 * the two ears combine. Effect is real for a subset of users; we don't
 * claim medical efficacy.
 *
 * The graph wiring (createBinaural) lives in graph.ts; this file
 * holds the type definitions + preset table + the math for "given a
 * band, what carrier/beat frequencies do I emit?"
 */

export type FrequencyBand = 'delta' | 'theta' | 'alpha' | 'beta' | 'gamma';

export interface BinauralPreset {
  id: string;
  band: FrequencyBand;
  /** Centre carrier frequency in Hz (perceived pitch). */
  carrierHz: number;
  /** Beat frequency in Hz = abs(left - right). */
  beatHz: number;
  /** Duration of the preset, ms (informational; user controls actual playback). */
  durationMs: number;
}

export const bandRange: Record<FrequencyBand, [number, number]> = {
  delta: [1, 4],
  theta: [4, 8],
  alpha: [8, 14],
  beta: [14, 30],
  gamma: [30, 100],
};

export const DEFAULT_PRESETS: readonly BinauralPreset[] = [
  { id: 'delta-rest', band: 'delta', carrierHz: 110, beatHz: 2, durationMs: 60 * 60_000 },
  { id: 'theta-flow', band: 'theta', carrierHz: 220, beatHz: 6, durationMs: 45 * 60_000 },
  { id: 'alpha-calm', band: 'alpha', carrierHz: 220, beatHz: 10, durationMs: 30 * 60_000 },
  { id: 'beta-work', band: 'beta', carrierHz: 200, beatHz: 18, durationMs: 25 * 60_000 },
  { id: 'gamma-sharp', band: 'gamma', carrierHz: 250, beatHz: 40, durationMs: 20 * 60_000 },
] as const;

export function presetById(id: string): BinauralPreset | null {
  return DEFAULT_PRESETS.find((p) => p.id === id) ?? null;
}

/**
 * Compute the two oscillator frequencies for a binaural pair.
 * Returns { leftHz, rightHz } such that abs(leftHz - rightHz) === beatHz
 * and the pair is centred on carrierHz.
 */
export function pairFrequencies(preset: BinauralPreset): {
  leftHz: number;
  rightHz: number;
} {
  const half = preset.beatHz / 2;
  return {
    leftHz: preset.carrierHz - half,
    rightHz: preset.carrierHz + half,
  };
}

/**
 * Validate a custom preset built by the user. Returns the typed preset
 * on success or an error string.
 */
export function validatePreset(
  candidate: Partial<BinauralPreset>
): { ok: true; preset: BinauralPreset } | { ok: false; error: string } {
  if (!candidate.id) return { ok: false, error: 'id required' };
  if (!candidate.band) return { ok: false, error: 'band required' };
  if (!candidate.carrierHz || candidate.carrierHz < 50 || candidate.carrierHz > 800) {
    return { ok: false, error: 'carrierHz must be 50..800 Hz' };
  }
  const [lo, hi] = bandRange[candidate.band];
  if (!candidate.beatHz || candidate.beatHz < lo || candidate.beatHz > hi) {
    return { ok: false, error: `beatHz must be in band ${candidate.band} (${lo}..${hi} Hz)` };
  }
  return {
    ok: true,
    preset: {
      id: candidate.id,
      band: candidate.band,
      carrierHz: candidate.carrierHz,
      beatHz: candidate.beatHz,
      durationMs: candidate.durationMs ?? 30 * 60_000,
    },
  };
}
