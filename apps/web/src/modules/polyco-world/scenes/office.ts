/**
 * Lane C Task C6 — Office scene data.
 *
 * The Phase-1 Office is an 8×8 room with floor tiles, walls along the
 * back two edges, a door on the south wall, the hero at centre, and
 * a graduated set of decoration unlocks that visibly populate as the
 * user completes sessions across modules.
 *
 * Co-located with the webapp because Phase-1 assets ship from
 * apps/web/public/. When the asset pipeline (Task C1) and Cloudflare R2
 * (Phase 2) land, this moves to content/scenes/office.json.
 */

import type { SceneJson } from '@njz-os/polyworld';

const SIZE = 8;

function floor(x: number, y: number): SceneJson['tiles'][number][number] {
  return { id: `floor-${x}-${y}`, kind: 'floor', spriteId: 'floor-wood', walkable: true };
}
function wall(x: number, y: number): SceneJson['tiles'][number][number] {
  return { id: `wall-${x}-${y}`, kind: 'wall', spriteId: 'wall-brick', walkable: false };
}
function door(x: number, y: number): SceneJson['tiles'][number][number] {
  return { id: `door-${x}-${y}`, kind: 'door', spriteId: 'door-oak', walkable: true };
}

const tiles: SceneJson['tiles'] = Array.from({ length: SIZE }, (_, ty) =>
  Array.from({ length: SIZE }, (_, tx) => {
    if (ty === 0) return wall(tx, ty);
    if (tx === 0) return wall(tx, ty);
    if (ty === SIZE - 1 && tx === Math.floor(SIZE / 2)) return door(tx, ty);
    if (ty === SIZE - 1) return wall(tx, ty);
    if (tx === SIZE - 1) return wall(tx, ty);
    return floor(tx, ty);
  })
);

export const OFFICE_SCENE: SceneJson = {
  id: 'office',
  kind: 'office',
  size: [SIZE, SIZE],
  tiles,
  decorations: [
    {
      id: 'desk',
      kind: 'furniture',
      spriteId: 'desk-pixel',
      position: [3, 2],
      unlockedBy: 'focus-hero.session.complete:1',
      fromModule: 'focus-hero',
    },
    {
      id: 'lamp-warm',
      kind: 'light',
      spriteId: 'lamp-warm',
      position: [3, 1],
      unlockedBy: 'focus-hero.session.complete:3',
      fromModule: 'focus-hero',
    },
    {
      id: 'trophy-bronze',
      kind: 'trophy',
      spriteId: 'trophy-bronze',
      position: [5, 1],
      unlockedBy: 'focus-hero.session.complete:10',
      fromModule: 'focus-hero',
    },
    {
      id: 'bookshelf',
      kind: 'furniture',
      spriteId: 'bookshelf',
      position: [1, 2],
      unlockedBy: 'writing-space.session.complete:1',
      fromModule: 'writing-space',
    },
    {
      id: 'memory-tome',
      kind: 'wall-art',
      spriteId: 'memory-tome',
      position: [1, 4],
      unlockedBy: 'micro-learning.session.complete:5',
      fromModule: 'micro-learning',
    },
    {
      id: 'plant-fern',
      kind: 'plant',
      spriteId: 'plant-fern',
      position: [5, 5],
      unlockedBy: 'streak.extend:7',
    },
    {
      id: 'banner-flow',
      kind: 'wall-art',
      spriteId: 'banner-flow',
      position: [5, 1],
      unlockedBy: 'brain-training.session.complete:5',
      fromModule: 'brain-training',
    },
  ],
  actors: [
    {
      id: 'hero',
      kind: 'hero',
      spriteId: 'hero-idle',
      position: [4, 4],
      facing: 's',
    },
  ],
};
