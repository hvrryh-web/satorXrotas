/**
 * Lane B Task B2 — Soundscape manifest schema.
 *
 * Every soundscape ships as a directory under
 *   apps/web/public/audio/stems/<id>/
 * containing a manifest.json + the actual audio stems. The manifest
 * describes the loop length, gapless overlap, and per-stem URLs +
 * codecs (AAC primary, Ogg fallback for Firefox).
 *
 * Schema-first: every fetched manifest runs through zod parse and
 * fails loudly with a typed error rather than producing a half-loaded
 * soundscape.
 */

import { z } from 'zod';

export const codecSchema = z.enum(['aac', 'ogg', 'mp3', 'opus']);
export type Codec = z.infer<typeof codecSchema>;

export const stemFileSchema = z.object({
  url: z.string().min(1),
  codec: codecSchema,
  /** Approximate bytes (for prefetch budgeting). */
  bytes: z.number().int().positive().optional(),
});
export type StemFile = z.infer<typeof stemFileSchema>;

export const stemSchema = z.object({
  /** Stem identity inside this soundscape; used as the mixer-track key. */
  id: z.string().min(1),
  /** Loop length in seconds (ADR-0010 default 300 = 5 min). */
  loopSeconds: z.number().positive(),
  /** Default gain at load time, 0..1. */
  defaultGain: z.number().min(0).max(1).default(0.85),
  /** Per-stem stereo pan, -1..1; 0 = centre. */
  pan: z.number().min(-1).max(1).default(0),
  /** One file per codec; the loader picks the first one the browser can decode. */
  files: z.array(stemFileSchema).min(1),
});
export type Stem = z.infer<typeof stemSchema>;

export const soundscapeCategorySchema = z.enum([
  'focus',
  'relax',
  'sleep',
  'meditate',
]);
export type SoundscapeCategory = z.infer<typeof soundscapeCategorySchema>;

export const soundscapeThemeSchema = z.enum([
  'nature',
  'urban',
  'cosmic',
  'minimal',
  'instrumental',
]);
export type SoundscapeTheme = z.infer<typeof soundscapeThemeSchema>;

export const soundscapeManifestSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  category: soundscapeCategorySchema,
  theme: soundscapeThemeSchema,
  /** Gapless overlap window in seconds (ADR-0010 §4 default 5). */
  crossfadeSeconds: z.number().positive().max(15).default(5),
  /** Total target duration of the loop family in seconds. */
  durationSeconds: z.number().positive(),
  stems: z.array(stemSchema).min(1),
  isPremium: z.boolean().default(false),
  /** Optional binaural overlay preset id (matches binaural.ts). */
  binauralPresetId: z.string().optional(),
  /** Optional cover art URL. */
  artUrl: z.string().optional(),
  /** Free-form attribution / credit line. */
  credit: z.string().optional(),
});
export type SoundscapeManifest = z.infer<typeof soundscapeManifestSchema>;

export class ManifestParseError extends Error {
  constructor(
    message: string,
    public readonly issues: unknown
  ) {
    super(message);
    this.name = 'ManifestParseError';
  }
}

export function parseManifest(raw: unknown): SoundscapeManifest {
  const result = soundscapeManifestSchema.safeParse(raw);
  if (!result.success) {
    throw new ManifestParseError(
      `Invalid soundscape manifest: ${result.error.message}`,
      result.error.issues
    );
  }
  return result.data;
}

/**
 * Browser-codec preference order: AAC primary, Ogg fallback (Firefox),
 * MP3 last-resort, Opus for forward-compatibility. Override per session
 * if the consumer wants a deterministic pick.
 */
export const DEFAULT_CODEC_PREFERENCE: readonly Codec[] = [
  'aac',
  'ogg',
  'opus',
  'mp3',
] as const;

/**
 * Pick the best stem file the browser can decode. Returns null if no
 * file matches the preference list — caller surfaces a user-facing
 * error.
 */
export function selectStemFile(
  stem: Stem,
  canDecode: (codec: Codec) => boolean,
  preference: readonly Codec[] = DEFAULT_CODEC_PREFERENCE
): StemFile | null {
  for (const codec of preference) {
    const match = stem.files.find((f) => f.codec === codec && canDecode(codec));
    if (match) return match;
  }
  return null;
}
