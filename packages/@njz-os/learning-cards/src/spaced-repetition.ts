export type Quality = 0 | 1 | 2 | 3 | 4 | 5;

export interface ReviewSchedule {
  cardId: string;
  intervalDays: number;
  easeFactor: number;
  repetitions: number;
  nextReviewAt: string;
}
