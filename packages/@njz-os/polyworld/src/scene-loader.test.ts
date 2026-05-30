import { describe, expect, it } from 'vitest';
import {
  SceneParseError,
  decorationIsUnlocked,
  parseScene,
  parseUnlockRule,
  unlockedDecorations,
} from './scene-loader';
import type { ProgressionEvent } from '@njz-os/core';

const OFFICE: Parameters<typeof parseScene>[0] = {
  id: 'office',
  kind: 'office',
  size: [8, 8],
  tiles: Array.from({ length: 4 }, () =>
    Array.from(
      { length: 4 },
      () => ({ id: 't', kind: 'floor' as const, spriteId: 'floor-wood', walkable: true })
    )
  ),
  decorations: [
    {
      id: 'trophy-focus-5',
      kind: 'trophy',
      spriteId: 'trophy-bronze',
      position: [2, 2],
      unlockedBy: 'focus-hero.session.complete:5',
      fromModule: 'focus-hero',
    },
    {
      id: 'streak-banner',
      kind: 'wall-art',
      spriteId: 'banner-7',
      position: [3, 3],
      unlockedBy: 'streak.extend:7',
    },
    {
      id: 'always-locked',
      kind: 'plant',
      spriteId: 'plant',
      position: [0, 0],
      unlockedBy: 'session.complete:999',
    },
  ],
  actors: [
    {
      id: 'hero',
      kind: 'hero',
      spriteId: 'hero-idle',
      position: [1, 1],
      facing: 's',
    },
  ],
};

describe('parseScene', () => {
  it('parses a complete scene', () => {
    const scene = parseScene(OFFICE, 'w_1');
    expect(scene.kind).toBe('office');
    expect(scene.tiles).toHaveLength(4);
    expect(scene.actors[0]?.id).toBe('hero');
  });

  it('throws SceneParseError on missing kind', () => {
    expect(() =>
      parseScene({ ...OFFICE, kind: undefined as unknown as 'office' }, 'w_1')
    ).toThrow(SceneParseError);
  });

  it('rejects invalid facing direction', () => {
    expect(() =>
      parseScene(
        {
          ...OFFICE,
          actors: [{ ...OFFICE.actors[0]!, facing: 'up' as unknown as 'n' }],
        },
        'w_1'
      )
    ).toThrow(SceneParseError);
  });
});

describe('parseUnlockRule', () => {
  it('parses qualified rule with module prefix', () => {
    expect(parseUnlockRule('focus-hero.session.complete:5')).toEqual({
      eventKind: 'session.complete',
      moduleFilter: 'focus-hero',
      threshold: 5,
    });
  });

  it('parses unqualified rule', () => {
    expect(parseUnlockRule('session.complete:3')).toEqual({
      eventKind: 'session.complete',
      moduleFilter: undefined,
      threshold: 3,
    });
  });

  it('returns null on malformed rule', () => {
    expect(parseUnlockRule('not-a-rule')).toBeNull();
  });
});

const userId = 'u_1' as unknown as ProgressionEvent extends { userId: infer U } ? U : never;
const sessionId = 's_1' as unknown as ProgressionEvent extends { sessionId: infer S } ? S : never;

function makeEvent(over: Partial<Extract<ProgressionEvent, { kind: 'session.complete' }>>): ProgressionEvent {
  return {
    kind: 'session.complete',
    userId,
    sessionId,
    module: 'focus-hero',
    durationMs: 25 * 60_000,
    xpAwarded: 25,
    at: '2026-05-30T00:00:00.000Z',
    ...over,
  };
}

describe('decorationIsUnlocked', () => {
  it('unlocks after threshold of matching events', () => {
    const events = Array.from({ length: 5 }, () => makeEvent({}));
    expect(
      decorationIsUnlocked(OFFICE.decorations[0]!, events)
    ).toBe(true);
  });

  it('stays locked when below threshold', () => {
    const events = Array.from({ length: 3 }, () => makeEvent({}));
    expect(
      decorationIsUnlocked(OFFICE.decorations[0]!, events)
    ).toBe(false);
  });

  it('honours module filter', () => {
    const events = Array.from({ length: 5 }, () =>
      makeEvent({ module: 'soundscapes' })
    );
    expect(
      decorationIsUnlocked(OFFICE.decorations[0]!, events)
    ).toBe(false);
  });

  it('streak.extend uses newCurrent ≥ threshold semantics', () => {
    const events: ProgressionEvent[] = [
      {
        kind: 'streak.extend',
        userId,
        module: 'focus-hero',
        newCurrent: 7,
        at: '2026-05-30T00:00:00.000Z',
      },
    ];
    expect(
      decorationIsUnlocked(OFFICE.decorations[1]!, events)
    ).toBe(true);
  });
});

describe('unlockedDecorations', () => {
  it('returns only the decorations whose rules pass', () => {
    const scene = parseScene(OFFICE, 'w_1');
    const events: ProgressionEvent[] = [
      ...Array.from({ length: 5 }, () => makeEvent({})),
      {
        kind: 'streak.extend',
        userId,
        module: 'focus-hero',
        newCurrent: 7,
        at: '2026-05-30T00:00:00.000Z',
      },
    ];
    const unlocked = unlockedDecorations(scene, events);
    expect(unlocked.map((d) => d.id).sort()).toEqual([
      'streak-banner',
      'trophy-focus-5',
    ]);
  });
});
