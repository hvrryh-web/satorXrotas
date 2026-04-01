import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';
import type {
  ExtendedPlayer,
  PlayerListResponse,
  ExtendedMatch,
  SimRatingBreakdown,
  RARResponse,
  InvestmentGradeResponse,
  SATOREvent,
  AREPOMarker,
  ROTASTrail,
  DashboardStats,
  PlayerFilters,
  MatchFilters,
} from '../types';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor for auth tokens or other headers
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token here if needed
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data as { detail?: string };
      
      switch (status) {
        case 404:
          console.error('Resource not found:', data?.detail);
          break;
        case 422:
          console.error('Validation error:', data?.detail);
          break;
        case 500:
          console.error('Server error:', data?.detail);
          break;
        default:
          console.error(`API Error (${status}):`, data?.detail || error.message);
      }
    } else if (error.request) {
      // Request was made but no response received
      console.error('Network error - no response received');
    } else {
      // Something else happened
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Type-safe API wrapper
async function apiRequest<T>(config: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.request<T>(config);
  return response.data;
}

// Players API
export const playersApi = {
  // Get list of players with filters
  getPlayers: async (
    filters: PlayerFilters = {},
    offset: number = 0,
    limit: number = 50
  ): Promise<PlayerListResponse> => {
    const params = new URLSearchParams();
    
    if (filters.region) params.append('region', filters.region);
    if (filters.role) params.append('role', filters.role);
    if (filters.minMaps) params.append('min_maps', filters.minMaps.toString());
    if (filters.grade) params.append('grade', filters.grade);
    params.append('offset', offset.toString());
    params.append('limit', limit.toString());

    return apiRequest<PlayerListResponse>({
      method: 'GET',
      url: '/api/players/',
      params,
    });
  },

  // Get single player by ID
  getPlayer: async (playerId: string): Promise<ExtendedPlayer> => {
    return apiRequest<ExtendedPlayer>({
      method: 'GET',
      url: `/api/players/${playerId}`,
    });
  },

  // Search players by name
  searchPlayers: async (query: string): Promise<ExtendedPlayer[]> => {
    const response = await playersApi.getPlayers({ search: query }, 0, 20);
    // Filter client-side for name matching if API doesn't support search
    return response.players.filter((p) =>
      p.name.toLowerCase().includes(query.toLowerCase()) ||
      (p.team && p.team.toLowerCase().includes(query.toLowerCase()))
    );
  },
};

// Matches API
export const matchesApi = {
  // Get list of matches with filters
  getMatches: async (filters: MatchFilters = {}): Promise<ExtendedMatch[]> => {
    const params = new URLSearchParams();
    
    if (filters.status) params.append('status', filters.status);
    if (filters.map) params.append('map', filters.map);
    if (filters.tournament) params.append('tournament', filters.tournament);
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);

    return apiRequest<ExtendedMatch[]>({
      method: 'GET',
      url: '/api/matches',
      params,
    });
  },

  // Get single match by ID
  getMatch: async (matchId: string): Promise<ExtendedMatch> => {
    return apiRequest<ExtendedMatch>({
      method: 'GET',
      url: `/api/matches/${matchId}`,
    });
  },

  // Get SATOR events for a specific round
  getSATOREvents: async (matchId: string, roundNumber: number): Promise<SATOREvent[]> => {
    return apiRequest<SATOREvent[]>({
      method: 'GET',
      url: `/api/matches/${matchId}/rounds/${roundNumber}/sator-events`,
    });
  },

  // Get AREPO markers for a specific round
  getAREPOMarkers: async (matchId: string, roundNumber: number): Promise<AREPOMarker[]> => {
    return apiRequest<AREPOMarker[]>({
      method: 'GET',
      url: `/api/matches/${matchId}/rounds/${roundNumber}/arepo-markers`,
    });
  },

  // Get ROTAS trails for a specific round
  getROTASTrails: async (matchId: string, roundNumber: number): Promise<ROTASTrail[]> => {
    return apiRequest<ROTASTrail[]>({
      method: 'GET',
      url: `/api/matches/${matchId}/rounds/${roundNumber}/rotas-trails`,
    });
  },
};

// Analytics API
export const analyticsApi = {
  // Get SimRating breakdown for a player
  getSimRating: async (playerId: string, season?: string): Promise<SimRatingBreakdown> => {
    const params = new URLSearchParams();
    if (season) params.append('season', season);

    return apiRequest<SimRatingBreakdown>({
      method: 'GET',
      url: `/api/analytics/simrating/${playerId}`,
      params,
    });
  },

  // Get RAR score for a player
  getRAR: async (playerId: string): Promise<RARResponse> => {
    return apiRequest<RARResponse>({
      method: 'GET',
      url: `/api/analytics/rar/${playerId}`,
    });
  },

  // Get investment grade for a player
  getInvestmentGrade: async (playerId: string): Promise<InvestmentGradeResponse> => {
    return apiRequest<InvestmentGradeResponse>({
      method: 'GET',
      url: `/api/analytics/investment/${playerId}`,
    });
  },

  // Get dashboard stats
  getDashboardStats: async (): Promise<DashboardStats> => {
    // This is a composite endpoint - in a real implementation,
    // this might be a dedicated endpoint or we compose it from multiple calls
    const [players, matches] = await Promise.all([
      playersApi.getPlayers({}, 0, 5),
      matchesApi.getMatches({ status: 'live' }),
    ]);

    return {
      totalMatches: 12400, // These would come from a stats endpoint
      totalPlayers: 2847,
      totalTournaments: 156,
      liveMatches: matches.length,
      topPlayers: players.players.slice(0, 5),
      recentMatches: [],
    };
  },
};

// Export the raw client for custom requests
export { apiClient };

// Default export with all APIs
export default {
  players: playersApi,
  matches: matchesApi,
  analytics: analyticsApi,
};
