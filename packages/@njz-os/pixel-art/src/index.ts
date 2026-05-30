export interface SpriteSheet {
  id: string;
  src: string;
  tileSize: number;
  cols: number;
  rows: number;
}

export interface SpriteFrame {
  sheetId: string;
  index: number;
}

export interface SpriteAnimation {
  id: string;
  frames: SpriteFrame[];
  fps: number;
  loop: boolean;
}

export * from './loader';
