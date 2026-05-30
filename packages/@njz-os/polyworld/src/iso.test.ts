import { describe, expect, it } from 'vitest';
import {
  TILE_H,
  TILE_W,
  isTileVisible,
  isoDepthKey,
  screenToTile,
  tileToScreen,
} from './iso';

describe('tileToScreen', () => {
  it('origin tile projects to origin', () => {
    expect(tileToScreen(0, 0)).toEqual({ sx: 0, sy: 0 });
  });

  it('tile (1, 0) shifts right + down by half-tile', () => {
    expect(tileToScreen(1, 0)).toEqual({ sx: TILE_W / 2, sy: TILE_H / 2 });
  });

  it('tile (0, 1) shifts left + down by half-tile', () => {
    expect(tileToScreen(0, 1)).toEqual({ sx: -TILE_W / 2, sy: TILE_H / 2 });
  });

  it('symmetric pair (1, 1) lands at (0, tileH)', () => {
    expect(tileToScreen(1, 1)).toEqual({ sx: 0, sy: TILE_H });
  });

  it('honours origin offset', () => {
    expect(tileToScreen(0, 0, { ox: 100, oy: 50 })).toEqual({ sx: 100, sy: 50 });
  });
});

describe('screenToTile (inverse)', () => {
  it('round-trips for integer tiles', () => {
    for (const tx of [0, 1, 2, 5]) {
      for (const ty of [0, 1, 2, 5]) {
        const { sx, sy } = tileToScreen(tx, ty);
        const result = screenToTile(sx + 1, sy + 1);
        expect(result.tx).toBe(tx);
        expect(result.ty).toBe(ty);
      }
    }
  });
});

describe('isoDepthKey', () => {
  it('row-major order — back tiles paint first', () => {
    const back = isoDepthKey(0, 0, 0);
    const front = isoDepthKey(2, 2, 0);
    expect(back).toBeLessThan(front);
  });

  it('z lift overrides ground tiles', () => {
    const ground = isoDepthKey(1, 1, 0);
    const decoration = isoDepthKey(1, 1, 2);
    expect(decoration).toBeGreaterThan(ground);
  });
});

describe('isTileVisible', () => {
  it('returns true for in-frame tile', () => {
    expect(
      isTileVisible(2, 2, { ox: 100, oy: 50 }, { w: 320, h: 240 })
    ).toBe(true);
  });

  it('culls tiles too far right', () => {
    expect(
      isTileVisible(100, 0, { ox: 0, oy: 0 }, { w: 320, h: 240 })
    ).toBe(false);
  });

  it('culls tiles far above the viewport (negative sy)', () => {
    expect(
      isTileVisible(-100, -100, { ox: 0, oy: 0 }, { w: 320, h: 240 })
    ).toBe(false);
  });
});
