/**
 * @sator/stats-schema
 *
 * Single source of truth for all SATOR public statistics.
 *
 * These types define ONLY what may be exposed to the web platform.
 * Do NOT add game-internal fields here (see docs/FIREWALL_POLICY.md).
 *
 * All public stats data flows through these types:
 *   Game → FantasyDataFilter → API → stats-schema types → Web
 */

// Player identity and basic info
export type { Player } from './Player';

// Match metadata
export type { Match } from './Match';

// Season and ranking data
export type { Season } from './Season';

// Player statistics (kills, deaths, assists, damage, etc.)
export type { Statistics } from './Statistics';
