import type { WorldId } from '@njz-os/core';
import type { TileGrid } from './tile';
import type { Decoration } from './decoration';
import type { Actor } from './actor';

export type SceneKind = 'office' | 'home' | 'visit';

export interface Scene {
  worldId: WorldId;
  kind: SceneKind;
  tiles: TileGrid;
  decorations: Decoration[];
  actors: Actor[];
  size: [number, number];
}
