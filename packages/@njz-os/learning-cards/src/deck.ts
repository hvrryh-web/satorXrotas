import type { Card } from './card';

export type DeckKind = 'quick-read' | 'series' | 'deep-dive';

export interface Deck {
  id: string;
  title: string;
  kind: DeckKind;
  cards: Card[];
  estimatedMinutes: number;
}
