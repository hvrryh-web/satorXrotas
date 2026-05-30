/**
 * Lane C Task C4 — Isometric projection math.
 *
 * Pure functions; no Canvas. Renderer (renderer.ts) consumes these to
 * project tile coordinates into screen-pixel coordinates.
 *
 * Tile coordinates: integer (tx, ty) — grid cells.
 * Screen coordinates: float (sx, sy) — pixels into the canvas.
 *
 * Tile size + isometric ratio per ADR-0005:
 *   tile width = 16 px, tile depth = 8 px (2:1 ratio)
 *
 * Y axis grows downward in screen space (standard Canvas 2D).
 * For a tile (tx, ty):
 *   sx = (tx - ty) * (TILE_W / 2)
 *   sy = (tx + ty) * (TILE_H / 2)
 *
 * The world origin (0, 0) projects to screen-x = 0; consumers add an
 * `origin` offset so the scene sits comfortably inside the canvas.
 */

export const TILE_W = 16;
export const TILE_H = 8;

export interface IsoPoint {
  sx: number;
  sy: number;
}

export interface ScreenOrigin {
  ox: number;
  oy: number;
}

export function tileToScreen(
  tx: number,
  ty: number,
  origin: ScreenOrigin = { ox: 0, oy: 0 },
  tileW: number = TILE_W,
  tileH: number = TILE_H
): IsoPoint {
  return {
    sx: origin.ox + (tx - ty) * (tileW / 2),
    sy: origin.oy + (tx + ty) * (tileH / 2),
  };
}

/**
 * Inverse projection: which tile contains screen point (sx, sy)?
 * Useful for click + hover handlers.
 */
export function screenToTile(
  sx: number,
  sy: number,
  origin: ScreenOrigin = { ox: 0, oy: 0 },
  tileW: number = TILE_W,
  tileH: number = TILE_H
): { tx: number; ty: number } {
  const dx = sx - origin.ox;
  const dy = sy - origin.oy;
  const tx = dx / tileW + dy / tileH;
  const ty = dy / tileH - dx / tileW;
  return { tx: Math.floor(tx), ty: Math.floor(ty) };
}

/**
 * Painter's-algorithm sort key: tiles closer to the back paint first,
 * tiles closer to the front paint on top.
 *
 * Equivalent to "lower row first, then lower column" but mapped onto
 * isometric world coordinates so a tile at (3, 0) paints before (0, 3)
 * since (3 + 0) > (0 + 3) is false — they're equal; ties break by tx.
 */
export function isoDepthKey(tx: number, ty: number, z: number = 0): number {
  return (tx + ty) * 1000 + tx + z * 100_000;
}

/**
 * Cull a tile based on whether its bounding box intersects the viewport.
 * tileH × 2 = 16 px below the iso-y (some sprites are taller).
 */
export function isTileVisible(
  tx: number,
  ty: number,
  origin: ScreenOrigin,
  viewport: { w: number; h: number },
  tileW: number = TILE_W,
  tileH: number = TILE_H,
  spriteOverdraw: number = tileH * 2
): boolean {
  const { sx, sy } = tileToScreen(tx, ty, origin, tileW, tileH);
  if (sx + tileW < 0 || sx - tileW > viewport.w) return false;
  if (sy + spriteOverdraw < 0 || sy - tileH > viewport.h) return false;
  return true;
}
