import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getHealth,
  getPlayers,
  getPlayer,
  getSimRating,
  getRAR,
  getInvestmentGrade,
  getMatch,
  getSatorEvents,
  type PlayerListResponse,
  type Player,
  type SimRatingResponse,
  type RARResponse,
  type InvestmentGradeResponse,
} from '../lib/api'

// Query keys for cache management
export const queryKeys = {
  health: ['health'] as const,
  players: ['players'] as const,
  player: (id: string) => ['player', id] as const,
  simRating: (id: string, season?: string) => ['simRating', id, season] as const,
  rar: (id: string) => ['rar', id] as const,
  investment: (id: string) => ['investment', id] as const,
  match: (id: string) => ['match', id] as const,
  satorEvents: (matchId: string, round: number) => ['satorEvents', matchId, round] as const,
}

/**
 * Hook for API health check
 */
export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: getHealth,
    refetchInterval: 30000, // Refetch every 30 seconds
    retry: 3,
  })
}

/**
 * Hook for fetching players list
 */
export function usePlayers(params?: {
  region?: string
  role?: string
  min_maps?: number
  grade?: string
  limit?: number
  offset?: number
}) {
  return useQuery<PlayerListResponse>({
    queryKey: [...queryKeys.players, params],
    queryFn: () => getPlayers(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Hook for fetching single player
 */
export function usePlayer(playerId: string) {
  return useQuery<Player>({
    queryKey: queryKeys.player(playerId),
    queryFn: () => getPlayer(playerId),
    enabled: !!playerId,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Hook for fetching SimRating
 */
export function useSimRating(playerId: string, season?: string) {
  return useQuery<SimRatingResponse>({
    queryKey: queryKeys.simRating(playerId, season),
    queryFn: () => getSimRating(playerId, season),
    enabled: !!playerId,
  })
}

/**
 * Hook for fetching RAR
 */
export function useRAR(playerId: string) {
  return useQuery<RARResponse>({
    queryKey: queryKeys.rar(playerId),
    queryFn: () => getRAR(playerId),
    enabled: !!playerId,
  })
}

/**
 * Hook for fetching Investment Grade
 */
export function useInvestmentGrade(playerId: string) {
  return useQuery<InvestmentGradeResponse>({
    queryKey: queryKeys.investment(playerId),
    queryFn: () => getInvestmentGrade(playerId),
    enabled: !!playerId,
  })
}

/**
 * Hook for fetching match data
 */
export function useMatch(matchId: string) {
  return useQuery({
    queryKey: queryKeys.match(matchId),
    queryFn: () => getMatch(matchId),
    enabled: !!matchId,
  })
}

/**
 * Hook for fetching SATOR events
 */
export function useSatorEvents(matchId: string, roundNumber: number) {
  return useQuery({
    queryKey: queryKeys.satorEvents(matchId, roundNumber),
    queryFn: () => getSatorEvents(matchId, roundNumber),
    enabled: !!matchId && roundNumber > 0,
  })
}
