/**
 * Player — public player identity and profile data.
 *
 * Contains only information safe to expose on the web platform.
 * Game-internal identifiers (seedValue, internalAgentState, etc.)
 * are explicitly excluded — see docs/FIREWALL_POLICY.md.
 */
export interface Player {
  /** Unique player identifier (public) */
  id: string;
  /** Display name */
  username: string;
  /** Player region */
  region: string;
  /** Profile creation timestamp (ISO 8601) */
  createdAt: string;
  /** Current rank tier */
  rankTier: string;
  /** Current rank points */
  rankPoints: number;
}
