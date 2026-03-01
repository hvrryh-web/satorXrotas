/**
 * Statistics — public player performance statistics.
 *
 * Only aggregate stats safe for the web platform are included.
 * Internal simulation metrics (simulationTick, visionConeData, etc.)
 * are explicitly excluded — see docs/FIREWALL_POLICY.md.
 */
export interface Statistics {
  /** Player identifier this stat block belongs to */
  playerId: string;
  /** Match identifier */
  matchId: string;
  /** Total kills */
  kills: number;
  /** Total deaths */
  deaths: number;
  /** Total assists */
  assists: number;
  /** Total damage dealt */
  damage: number;
  /** Headshot kills */
  headshots: number;
  /** Utility (grenade) damage dealt */
  utilityDamage: number;
  /** Rounds won by the player's team */
  roundsWon: number;
  /** First kills in a round */
  firstKills: number;
  /** Clutch rounds won */
  clutchesWon: number;
}
