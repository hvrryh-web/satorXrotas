/**
 * Lane B — Soundscape descriptor (the catalogue row, separate from the
 * runtime manifest used by the loader).
 *
 * Used by the Soundscapes module home view to populate category tiles.
 */

import type {
  SoundscapeCategory,
  SoundscapeTheme,
} from './manifest';

export type { SoundscapeCategory, SoundscapeTheme } from './manifest';

export interface Soundscape {
  id: string;
  title: string;
  category: SoundscapeCategory;
  theme: SoundscapeTheme;
  /** Length of one looped session in ms; matches manifest.durationSeconds × 1000. */
  durationMs: number;
  /** Stem identifiers the manifest exposes. */
  stems: string[];
  isPremium: boolean;
  /** Optional binaural overlay preset (matches binaural.DEFAULT_PRESETS). */
  binauralPresetId?: string;
}

/** The 5 baseline soundscapes ADR-0010 requires for Phase 1. */
export const BASELINE_SOUNDSCAPES: readonly Soundscape[] = [
  {
    id: 'rain-on-leaves',
    title: 'Rain on leaves',
    category: 'relax',
    theme: 'nature',
    durationMs: 30 * 60_000,
    stems: ['rain-soft', 'leaves-wet'],
    isPremium: false,
  },
  {
    id: 'deep-forest',
    title: 'Deep forest',
    category: 'meditate',
    theme: 'nature',
    durationMs: 60 * 60_000,
    stems: ['canopy', 'distant-bird', 'wind-low'],
    isPremium: false,
  },
  {
    id: 'cafe-hum',
    title: 'Café hum',
    category: 'focus',
    theme: 'urban',
    durationMs: 25 * 60_000,
    stems: ['ambient-chatter', 'cup-clink'],
    isPremium: false,
    binauralPresetId: 'alpha-calm',
  },
  {
    id: 'cosmic-drift',
    title: 'Cosmic drift',
    category: 'sleep',
    theme: 'cosmic',
    durationMs: 90 * 60_000,
    stems: ['low-drone', 'shimmer'],
    isPremium: false,
    binauralPresetId: 'delta-rest',
  },
  {
    id: 'pixel-rain',
    title: 'Pixel rain',
    category: 'focus',
    theme: 'minimal',
    durationMs: 25 * 60_000,
    stems: ['arp-low', 'arp-high'],
    isPremium: false,
    binauralPresetId: 'beta-work',
  },
] as const;

export function soundscapesByCategory(
  category: SoundscapeCategory,
  catalogue: readonly Soundscape[] = BASELINE_SOUNDSCAPES
): readonly Soundscape[] {
  return catalogue.filter((s) => s.category === category);
}

export function soundscapeById(
  id: string,
  catalogue: readonly Soundscape[] = BASELINE_SOUNDSCAPES
): Soundscape | null {
  return catalogue.find((s) => s.id === id) ?? null;
}
