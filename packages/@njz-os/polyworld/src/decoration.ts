import type { ModuleSlug } from '@njz-os/core';

export interface Decoration {
  id: string;
  kind: 'trophy' | 'furniture' | 'wall-art' | 'light' | 'plant';
  spriteId: string;
  position: [number, number];
  unlockedBy: string;
  fromModule?: ModuleSlug;
}
