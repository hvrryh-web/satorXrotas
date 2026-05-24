export interface Card {
  id: string;
  illustration: string;
  headline: string;
  insight: string;
  detail?: string;
  tags: string[];
  connections: string[];
}
