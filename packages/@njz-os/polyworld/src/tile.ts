export interface Tile {
  id: string;
  kind: 'floor' | 'wall' | 'door' | 'feature';
  spriteId: string;
  walkable: boolean;
}

export type TileGrid = (Tile | null)[][];
