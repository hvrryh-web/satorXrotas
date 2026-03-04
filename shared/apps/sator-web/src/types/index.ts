/**
 * SATOR Web Platform Types
 * 
 * These types extend the base stats-schema types with additional
 * frontend-specific fields and API response types.
 */

// Re-export base types from stats-schema
export type { Player, Match, Statistics } from '@sator/stats-schema';

// Extended Player type with additional fields from the API
export interface ExtendedPlayer {
  player_id: string;
  name: string;
  team?: string;
  region?: string;
  role?: string;
  kills?: number;
  deaths?: number;
  acs?: number;
  adr?: number;
  kast_pct?: number;
  sim_rating?: number;
  rar_score?: number;
  investment_grade?: 'A+' | 'A' | 'B' | 'C' | 'D';
  confidence_tier?: number;
  map_count?: number;
}

// Player list response
export interface PlayerListResponse {
  players: ExtendedPlayer[];
  total: number;
  offset: number;
  limit: number;
}

// Extended Match type with team details
export interface ExtendedMatch {
  id: string;
  startedAt: string;
  endedAt: string;
  mapName: string;
  winnerSide: 'team_a' | 'team_b' | 'draw';
  roundsPlayed: number;
  playerIds: string[];
  teamA?: {
    name: string;
    score: number;
    players: string[];
  };
  teamB?: {
    name: string;
    score: number;
    players: string[];
  };
  status: 'live' | 'finished' | 'upcoming';
  tournament?: string;
}

// SimRating breakdown response
export interface SimRatingBreakdown {
  player_id: string;
  season?: string;
  sim_rating: number;
  components: {
    kills: number;
    deaths: number;
    adjusted_kill_value: number;
    adr: number;
    kast: number;
  };
  z_scores: {
    kills: number;
    deaths: number;
    adjusted_kill_value: number;
    adr: number;
    kast_pct: number;
  };
}

// RAR (Role-Adjusted value above Replacement) response
export interface RARResponse {
  player_id: string;
  role: string;
  raw_rating: number;
  replacement_level: number;
  rar_score: number;
  investment_grade: 'A+' | 'A' | 'B' | 'C' | 'D';
}

// Investment grade response
export interface InvestmentGradeResponse {
  player_id: string;
  grade: 'A+' | 'A' | 'B' | 'C' | 'D';
  value_score: number;
  age_factor: number;
  trend: 'up' | 'down' | 'stable';
}

// SATOR spatial event types
export interface SATOREvent {
  id: string;
  type: 'planter' | 'mvp' | 'hotstreak' | 'clutch';
  playerId: string;
  playerName: string;
  round: number;
  timestamp: string;
  description: string;
}

// AREPO marker (death stain)
export interface AREPOMarker {
  x: number;
  y: number;
  playerId: string;
  playerName: string;
  round: number;
  team: 'a' | 'b';
}

// ROTAS trail (rotation path)
export interface ROTASTrail {
  playerId: string;
  playerName: string;
  points: { x: number; y: number; timestamp: number }[];
  round: number;
  team: 'a' | 'b';
}

// Dashboard stats
export interface DashboardStats {
  totalMatches: number;
  totalPlayers: number;
  totalTournaments: number;
  liveMatches: number;
  topPlayers: ExtendedPlayer[];
  recentMatches: ExtendedMatch[];
}

// Filter options
export interface PlayerFilters {
  region?: string;
  role?: string;
  minMaps?: number;
  grade?: 'A+' | 'A' | 'B' | 'C' | 'D';
  search?: string;
}

export interface MatchFilters {
  status?: 'live' | 'finished' | 'upcoming';
  map?: string;
  tournament?: string;
  dateFrom?: string;
  dateTo?: string;
}

// Sort options
export type PlayerSortField = 
  | 'name' 
  | 'acs' 
  | 'adr' 
  | 'kast_pct' 
  | 'sim_rating' 
  | 'rar_score' 
  | 'map_count';

export type SortDirection = 'asc' | 'desc';

export interface SortOptions {
  field: PlayerSortField;
  direction: SortDirection;
}
