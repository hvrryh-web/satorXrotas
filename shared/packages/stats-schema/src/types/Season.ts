/**
 * Season — season and ranking data.
 *
 * Covers ranked-season metadata and leaderboard context.
 */
export interface Season {
  /** Season identifier */
  id: string;
  /** Human-readable season name (e.g. "Season 1") */
  name: string;
  /** UTC start date (ISO 8601) */
  startDate: string;
  /** UTC end date (ISO 8601) */
  endDate: string;
  /** Whether the season is currently active */
  isActive: boolean;
}
