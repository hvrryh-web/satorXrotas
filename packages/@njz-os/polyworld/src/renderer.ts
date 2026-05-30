/**
 * Lane C Task C4 — Canvas 2D isometric renderer.
 *
 * Mounts onto an HTMLCanvasElement and renders the scene each tick.
 * Painter's-algorithm sort + viewport culling per iso.ts. Sprites are
 * drawn nearest-neighbour by setting `imageSmoothingEnabled = false`
 * (pixel-art).
 *
 * Browser-only execution path. The math under iso.ts is testable in
 * Node; this file is dependency-injection-friendly so tests can pass
 * a mocked 2D context if needed.
 */

import type { Scene } from './scene';
import type { Tile } from './tile';
import type { Decoration } from './decoration';
import type { Actor } from './actor';
import {
  TILE_H,
  TILE_W,
  isTileVisible,
  isoDepthKey,
  tileToScreen,
  type ScreenOrigin,
} from './iso';

export interface Context2DLike {
  canvas: { width: number; height: number };
  imageSmoothingEnabled: boolean;
  clearRect(x: number, y: number, w: number, h: number): void;
  drawImage(
    image: CanvasImageSource,
    sx: number,
    sy: number,
    sw: number,
    sh: number,
    dx: number,
    dy: number,
    dw: number,
    dh: number
  ): void;
  fillStyle: string | CanvasGradient | CanvasPattern;
  fillRect(x: number, y: number, w: number, h: number): void;
}

export interface SpriteResolver {
  /** Look up an atlas frame by spriteId; null when not loaded. */
  (spriteId: string): {
    image: CanvasImageSource;
    sx: number;
    sy: number;
    sw: number;
    sh: number;
  } | null;
}

export interface RendererOptions {
  origin?: ScreenOrigin;
  background?: string;
  tileWidth?: number;
  tileHeight?: number;
  /** Optional debug overlay: draws tile coordinates over each cell. */
  debug?: boolean;
}

export interface RendererStats {
  tilesDrawn: number;
  decorationsDrawn: number;
  actorsDrawn: number;
  culled: number;
}

interface DrawCommand {
  kind: 'tile' | 'decoration' | 'actor';
  tx: number;
  ty: number;
  z: number;
  spriteId: string;
}

export function renderScene(
  ctx: Context2DLike,
  scene: Scene,
  resolveSprite: SpriteResolver,
  unlockedDecorationIds: ReadonlySet<string>,
  options: RendererOptions = {}
): RendererStats {
  const origin: ScreenOrigin = options.origin ?? {
    ox: ctx.canvas.width / 2,
    oy: 32,
  };
  const tileW = options.tileWidth ?? TILE_W;
  const tileH = options.tileHeight ?? TILE_H;

  ctx.imageSmoothingEnabled = false;
  ctx.fillStyle = options.background ?? '#0F172A';
  ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);

  const viewport = { w: ctx.canvas.width, h: ctx.canvas.height };
  const stats: RendererStats = {
    tilesDrawn: 0,
    decorationsDrawn: 0,
    actorsDrawn: 0,
    culled: 0,
  };

  const queue: DrawCommand[] = [];
  for (let ty = 0; ty < scene.tiles.length; ty += 1) {
    const row = scene.tiles[ty]!;
    for (let tx = 0; tx < row.length; tx += 1) {
      const tile: Tile | null = row[tx] ?? null;
      if (!tile) continue;
      if (!isTileVisible(tx, ty, origin, viewport, tileW, tileH)) {
        stats.culled += 1;
        continue;
      }
      queue.push({
        kind: 'tile',
        tx,
        ty,
        z: tile.kind === 'wall' || tile.kind === 'feature' ? 1 : 0,
        spriteId: tile.spriteId,
      });
    }
  }

  for (const d of scene.decorations) {
    if (!unlockedDecorationIds.has(d.id)) continue;
    const [tx, ty] = d.position;
    queue.push({ kind: 'decoration', tx, ty, z: 2, spriteId: d.spriteId });
  }

  for (const a of scene.actors) {
    const [tx, ty] = a.position;
    queue.push({ kind: 'actor', tx, ty, z: 3, spriteId: a.spriteId });
  }

  queue.sort((a, b) => isoDepthKey(a.tx, a.ty, a.z) - isoDepthKey(b.tx, b.ty, b.z));

  for (const cmd of queue) {
    const frame = resolveSprite(cmd.spriteId);
    if (!frame) continue;
    const { sx, sy } = tileToScreen(cmd.tx, cmd.ty, origin, tileW, tileH);
    const dy = sy - (frame.sh - tileH);
    ctx.drawImage(
      frame.image,
      frame.sx,
      frame.sy,
      frame.sw,
      frame.sh,
      sx - frame.sw / 2,
      dy,
      frame.sw,
      frame.sh
    );
    if (cmd.kind === 'tile') stats.tilesDrawn += 1;
    else if (cmd.kind === 'decoration') stats.decorationsDrawn += 1;
    else stats.actorsDrawn += 1;
  }

  return stats;
}

/**
 * Convenience: derive the unlocked-decoration ID set from the
 * unlocked-decorations list. Common caller path.
 */
export function unlockedSetFrom(
  unlocked: readonly Decoration[]
): ReadonlySet<string> {
  return new Set(unlocked.map((d) => d.id));
}

/**
 * Decide which actor sprite to draw given a stats vector — used to
 * give the hero a tier-themed look once Cognitive Profile lands.
 */
export function actorSpriteVariant(actor: Actor): string {
  return actor.aura ? `${actor.spriteId}-${actor.aura}` : actor.spriteId;
}
