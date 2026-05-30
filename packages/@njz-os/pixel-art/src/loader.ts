/**
 * Lane C Task C3 — Pixel-art sprite-sheet loader.
 *
 * Aseprite (--sheet packed --format json-hash) emits a JSON manifest
 * keyed by frame name + a single packed PNG. This loader consumes the
 * manifest, attaches the loaded HTMLImageElement, and resolves
 * `SpriteFrame`s by name or by index.
 *
 * Pure-data parsing lives here (parseAsepriteManifest); image loading
 * is browser-only and gated behind a small adapter so tests don't need
 * a DOM.
 */

import { z } from 'zod';

export const asepriteFrameSchema = z.object({
  frame: z.object({
    x: z.number().int().min(0),
    y: z.number().int().min(0),
    w: z.number().int().positive(),
    h: z.number().int().positive(),
  }),
  duration: z.number().int().nonnegative().default(100),
  trimmed: z.boolean().default(false),
});
export type AsepriteFrame = z.infer<typeof asepriteFrameSchema>;

export const asepriteMetaSchema = z.object({
  image: z.string().min(1),
  size: z.object({ w: z.number().positive(), h: z.number().positive() }),
  scale: z.string().optional(),
});

export const asepriteManifestSchema = z.object({
  frames: z.record(z.string(), asepriteFrameSchema),
  meta: asepriteMetaSchema,
});
export type AsepriteManifest = z.infer<typeof asepriteManifestSchema>;

export class SpriteSheetParseError extends Error {
  constructor(message: string, public readonly issues: unknown) {
    super(message);
    this.name = 'SpriteSheetParseError';
  }
}

export interface SpriteSheetDescriptor {
  id: string;
  imageUrl: string;
  frames: Map<string, AsepriteFrame>;
  size: { w: number; h: number };
}

export function parseAsepriteManifest(
  id: string,
  raw: unknown,
  imageUrlOverride?: string
): SpriteSheetDescriptor {
  const parsed = asepriteManifestSchema.safeParse(raw);
  if (!parsed.success) {
    throw new SpriteSheetParseError(
      `sprite-sheet manifest for ${id} failed schema`,
      parsed.error.issues
    );
  }
  return {
    id,
    imageUrl: imageUrlOverride ?? parsed.data.meta.image,
    frames: new Map(Object.entries(parsed.data.frames)),
    size: parsed.data.meta.size,
  };
}

export interface ResolvedSpriteFrame {
  sheetId: string;
  name: string;
  sx: number;
  sy: number;
  sw: number;
  sh: number;
}

/**
 * Look up a frame by name. Returns null when missing so the caller
 * can fall back to a placeholder rather than crashing the renderer.
 */
export function resolveFrame(
  sheet: SpriteSheetDescriptor,
  name: string
): ResolvedSpriteFrame | null {
  const f = sheet.frames.get(name);
  if (!f) return null;
  return {
    sheetId: sheet.id,
    name,
    sx: f.frame.x,
    sy: f.frame.y,
    sw: f.frame.w,
    sh: f.frame.h,
  };
}

/** Convenience: list all known frame names (for editor tools). */
export function listFrameNames(sheet: SpriteSheetDescriptor): string[] {
  return Array.from(sheet.frames.keys()).sort();
}

/**
 * Browser-only: actually load the image. Returns a promise resolving
 * to the loaded HTMLImageElement, or rejects with the failure reason.
 * Caller is responsible for retaining the reference until done.
 */
export function loadSpriteImage(url: string): Promise<HTMLImageElement> {
  if (typeof Image === 'undefined') {
    return Promise.reject(
      new Error('loadSpriteImage requires a browser environment')
    );
  }
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = (): void => resolve(img);
    img.onerror = (): void => reject(new Error(`failed to load sprite image ${url}`));
    img.src = url;
  });
}
