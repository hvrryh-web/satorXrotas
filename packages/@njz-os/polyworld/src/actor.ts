export type ActorKind = 'hero' | 'npc';

export interface ActorStats {
  focus: number;
  creativity: number;
  wellness: number;
  knowledge: number;
}

export interface Actor {
  id: string;
  kind: ActorKind;
  spriteId: string;
  position: [number, number];
  facing: 'n' | 'e' | 's' | 'w';
  stats?: ActorStats;
  title?: string;
  aura?: string;
}
