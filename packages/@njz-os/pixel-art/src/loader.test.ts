import { describe, expect, it } from 'vitest';
import {
  parseAsepriteManifest,
  resolveFrame,
  listFrameNames,
  SpriteSheetParseError,
} from './loader';

const VALID = {
  meta: { image: 'office.png', size: { w: 256, h: 128 } },
  frames: {
    'floor-wood': { frame: { x: 0, y: 0, w: 16, h: 16 }, duration: 100, trimmed: false },
    'wall-brick': { frame: { x: 16, y: 0, w: 16, h: 32 }, duration: 100, trimmed: false },
    'hero-idle-0': { frame: { x: 32, y: 0, w: 16, h: 24 }, duration: 100, trimmed: false },
  },
};

describe('parseAsepriteManifest', () => {
  it('parses a valid manifest', () => {
    const sheet = parseAsepriteManifest('office', VALID);
    expect(sheet.id).toBe('office');
    expect(sheet.imageUrl).toBe('office.png');
    expect(sheet.frames.size).toBe(3);
    expect(sheet.size).toEqual({ w: 256, h: 128 });
  });

  it('honours an imageUrlOverride', () => {
    const sheet = parseAsepriteManifest('office', VALID, '/assets/office.png');
    expect(sheet.imageUrl).toBe('/assets/office.png');
  });

  it('throws SpriteSheetParseError on missing meta', () => {
    expect(() =>
      parseAsepriteManifest('x', { frames: VALID.frames })
    ).toThrow(SpriteSheetParseError);
  });

  it('rejects negative frame size', () => {
    expect(() =>
      parseAsepriteManifest('x', {
        meta: VALID.meta,
        frames: { bad: { frame: { x: 0, y: 0, w: -1, h: 16 } } },
      })
    ).toThrow(SpriteSheetParseError);
  });
});

describe('resolveFrame', () => {
  const sheet = parseAsepriteManifest('office', VALID);

  it('returns frame coordinates for a known name', () => {
    const frame = resolveFrame(sheet, 'wall-brick');
    expect(frame).toEqual({
      sheetId: 'office',
      name: 'wall-brick',
      sx: 16,
      sy: 0,
      sw: 16,
      sh: 32,
    });
  });

  it('returns null for unknown name', () => {
    expect(resolveFrame(sheet, 'nope')).toBeNull();
  });
});

describe('listFrameNames', () => {
  it('returns frame names sorted alphabetically', () => {
    const sheet = parseAsepriteManifest('office', VALID);
    expect(listFrameNames(sheet)).toEqual(['floor-wood', 'hero-idle-0', 'wall-brick']);
  });
});
