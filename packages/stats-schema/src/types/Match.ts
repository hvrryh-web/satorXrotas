/**
 * Match — public match metadata.
 *
 * Contains only summary information safe to expose on the web platform.
 * Per-tick simulation data, raycast frames, and seed values are excluded.
 */
export interface Match {
  /** Unique match identifier */
  id: string;
  /** UTC start time (ISO 8601) */
  startedAt: string;
  /** UTC end time (ISO 8601) */
  endedAt: string;
  /** Map name */
  mapName: string;
  /** Winning team side */
  winnerSide: 'team_a' | 'team_b' | 'draw';
  /** Number of rounds played */
  roundsPlayed: number;
  /** IDs of participating players */
  playerIds: string[];
}
