import { describe, expect, it } from 'vitest';
import {
  ManifestParseError,
  parseManifest,
  selectStemFile,
  DEFAULT_CODEC_PREFERENCE,
  type Codec,
  type Stem,
} from './manifest';

const VALID_MANIFEST = {
  id: 'rain-on-leaves',
  title: 'Rain on leaves',
  category: 'relax' as const,
  theme: 'nature' as const,
  durationSeconds: 1800,
  stems: [
    {
      id: 'rain-soft',
      loopSeconds: 300,
      files: [
        { url: '/audio/stems/rain-on-leaves/rain.aac', codec: 'aac' as const, bytes: 4_900_000 },
        { url: '/audio/stems/rain-on-leaves/rain.ogg', codec: 'ogg' as const, bytes: 5_300_000 },
      ],
    },
  ],
};

describe('parseManifest', () => {
  it('accepts a complete valid manifest', () => {
    const m = parseManifest(VALID_MANIFEST);
    expect(m.id).toBe('rain-on-leaves');
    expect(m.crossfadeSeconds).toBe(5);
    expect(m.stems[0]!.defaultGain).toBe(0.85);
  });

  it('applies stem defaults (defaultGain, pan)', () => {
    const m = parseManifest(VALID_MANIFEST);
    expect(m.stems[0]!.pan).toBe(0);
  });

  it('throws ManifestParseError on missing required fields', () => {
    const broken = { ...VALID_MANIFEST, id: undefined };
    expect(() => parseManifest(broken)).toThrow(ManifestParseError);
  });

  it('throws on out-of-range pan', () => {
    const broken = {
      ...VALID_MANIFEST,
      stems: [{ ...VALID_MANIFEST.stems[0]!, pan: 5 }],
    };
    expect(() => parseManifest(broken)).toThrow(ManifestParseError);
  });

  it('rejects empty stems array', () => {
    expect(() => parseManifest({ ...VALID_MANIFEST, stems: [] })).toThrow(
      ManifestParseError
    );
  });
});

describe('selectStemFile', () => {
  const stem: Stem = {
    id: 's',
    loopSeconds: 300,
    defaultGain: 0.85,
    pan: 0,
    files: [
      { url: 'a.aac', codec: 'aac' },
      { url: 'a.ogg', codec: 'ogg' },
      { url: 'a.mp3', codec: 'mp3' },
    ],
  };

  it('picks the first preferred codec the browser can decode', () => {
    const file = selectStemFile(stem, (c: Codec) => c === 'aac');
    expect(file?.codec).toBe('aac');
  });

  it('falls back to the next preferred codec', () => {
    const file = selectStemFile(stem, (c: Codec) => c === 'ogg');
    expect(file?.codec).toBe('ogg');
  });

  it('returns null if no preferred codec matches', () => {
    expect(selectStemFile(stem, () => false)).toBeNull();
  });

  it('respects an explicit preference override', () => {
    const file = selectStemFile(stem, () => true, ['mp3', 'aac']);
    expect(file?.codec).toBe('mp3');
  });

  it('DEFAULT_CODEC_PREFERENCE puts AAC first, Ogg second', () => {
    expect(DEFAULT_CODEC_PREFERENCE[0]).toBe('aac');
    expect(DEFAULT_CODEC_PREFERENCE[1]).toBe('ogg');
  });
});
