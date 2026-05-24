import type { CognitiveDomain } from './profile';

export type GameId =
  | 'stroop-test'
  | 'corsi-blocks'
  | 'digit-span'
  | 'memory-matrix'
  | 'match-pairs';

export interface WorkoutSlot {
  gameId: GameId;
  domain: CognitiveDomain;
  difficulty: number;
}

export interface WorkoutPlan {
  forUserAt: string;
  slots: [WorkoutSlot, WorkoutSlot, WorkoutSlot];
  rationale: 'strength' | 'weakness' | 'random';
}
