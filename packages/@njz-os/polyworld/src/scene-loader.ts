/**
 * Lane C Task C5 — Scene-loader + decoration unlock resolver.
 *
 * Parses scene JSON (zod-validated), produces a renderable Scene struct
 * with tile grid + decoration overlay + actors, and exposes a
 * `unlockedDecorations` selector that filters the scene's decorations
 * against a stream of completed ProgressionEvents.
 *
 * Decoration unlocks are declarative: each decoration carries an
 * `unlockedBy` rule (e.g. "focus.session.complete:5" — unlock after
 * 5 completed focus sessions). The resolver tallies events and returns
 * which decorations should be visible.
 *
 * Pure functions; rendering integration lives in renderer.ts.
 */

import { z } from 'zod';
import type { ProgressionEvent } from '@njz-os/core';
import type { Decoration } from './decoration';
import type { Scene } from './scene';

export const sceneJsonSchema = z.object({
  id: z.string().min(1),
  kind: z.enum(['office', 'home', 'visit']),
  size: z.tuple([z.number().int().positive(), z.number().int().positive()]),
  tiles: z.array(
    z.array(
      z
        .object({
          id: z.string().min(1),
          kind: z.enum(['floor', 'wall', 'door', 'feature']),
          spriteId: z.string().min(1),
          walkable: z.boolean(),
        })
        .nullable()
    )
  ),
  decorations: z.array(
    z.object({
      id: z.string().min(1),
      kind: z.enum(['trophy', 'furniture', 'wall-art', 'light', 'plant']),
      spriteId: z.string().min(1),
      position: z.tuple([z.number().int().min(0), z.number().int().min(0)]),
      unlockedBy: z.string().min(1),
      fromModule: z
        .enum([
          'focus-hero',
          'soundscapes',
          'distraction-blocker',
          'writing-space',
          'micro-learning',
          'brain-training',
          'polyco-world',
        ])
        .optional(),
    })
  ),
  actors: z.array(
    z.object({
      id: z.string().min(1),
      kind: z.enum(['hero', 'npc']),
      spriteId: z.string().min(1),
      position: z.tuple([z.number().int().min(0), z.number().int().min(0)]),
      facing: z.enum(['n', 'e', 's', 'w']),
      title: z.string().optional(),
      aura: z.string().optional(),
    })
  ),
});

export type SceneJson = z.infer<typeof sceneJsonSchema>;

export class SceneParseError extends Error {
  constructor(message: string, public readonly issues: unknown) {
    super(message);
    this.name = 'SceneParseError';
  }
}

export function parseScene(raw: unknown, worldId: string): Scene {
  const parsed = sceneJsonSchema.safeParse(raw);
  if (!parsed.success) {
    throw new SceneParseError(`scene JSON failed schema`, parsed.error.issues);
  }
  const data = parsed.data;
  return {
    worldId: worldId as Scene['worldId'],
    kind: data.kind,
    size: data.size,
    tiles: data.tiles,
    decorations: data.decorations,
    actors: data.actors,
  };
}

/**
 * Decoration unlock rules. Format: `<eventKind>:<threshold>` where:
 *   - eventKind matches a ProgressionEvent kind ("session.complete",
 *     "streak.extend", etc.) — optionally qualified by module
 *     ("focus.session.complete" → only focus-hero sessions count)
 *   - threshold is the integer count required to unlock.
 *
 * Examples:
 *   "session.complete:5"            → any 5 completed sessions
 *   "focus.session.complete:10"     → 10 completed focus sessions
 *   "writing.session.complete:1"    → first completed writing session
 *   "streak.extend:7"               → at least one 7-day streak
 */
export interface DecorationUnlockRule {
  eventKind: string;
  moduleFilter?: string;
  threshold: number;
}

const KNOWN_MODULE_SLUGS = [
  'focus-hero',
  'soundscapes',
  'distraction-blocker',
  'writing-space',
  'micro-learning',
  'brain-training',
  'polyco-world',
] as const;

const RULE_RE = /^(.+):(\d+)$/;

export function parseUnlockRule(raw: string): DecorationUnlockRule | null {
  const match = RULE_RE.exec(raw);
  if (!match) return null;
  const body = match[1]!;
  const threshold = Number(match[2]!);
  for (const slug of KNOWN_MODULE_SLUGS) {
    if (body.startsWith(`${slug}.`)) {
      return {
        eventKind: body.slice(slug.length + 1),
        moduleFilter: slug,
        threshold,
      };
    }
  }
  return { eventKind: body, threshold };
}

export function decorationIsUnlocked(
  decoration: Decoration,
  events: readonly ProgressionEvent[]
): boolean {
  const rule = parseUnlockRule(decoration.unlockedBy);
  if (!rule) return false;
  const matches = events.filter((e) => {
    if (rule.eventKind === 'streak.extend' && e.kind === 'streak.extend') {
      if (rule.moduleFilter && e.module !== rule.moduleFilter) return false;
      return e.newCurrent >= rule.threshold;
    }
    if (e.kind !== rule.eventKind) return false;
    if (rule.moduleFilter && 'module' in e && e.module !== rule.moduleFilter)
      return false;
    return true;
  });
  if (rule.eventKind === 'streak.extend') {
    return matches.length > 0;
  }
  return matches.length >= rule.threshold;
}

export function unlockedDecorations(
  scene: Scene,
  events: readonly ProgressionEvent[]
): Decoration[] {
  return scene.decorations.filter((d) => decorationIsUnlocked(d, events));
}
