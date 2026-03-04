import { useState, useCallback, useMemo } from 'react';
import { usePlayers as usePlayersQuery, usePlayerSearch } from './useApi';
import type { PlayerFilters, PlayerSortField, SortDirection, ExtendedPlayer } from '../types';

// Custom hook for player list with client-side sorting and filtering
export function usePlayerList(
  initialFilters: PlayerFilters = {},
  pageSize: number = 50
) {
  const [filters, setFilters] = useState<PlayerFilters>(initialFilters);
  const [sortField, setSortField] = useState<PlayerSortField>('sim_rating');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [page, setPage] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');

  // Use search hook when there's a search query, otherwise use list hook
  const {
    data: searchData,
    isLoading: isSearchLoading,
    error: searchError,
  } = usePlayerSearch(searchQuery, {
    enabled: searchQuery.length >= 2,
  });

  const {
    data: listData,
    isLoading: isListLoading,
    error: listError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = usePlayersQuery(filters, page * pageSize, pageSize);

  // Determine which data to use
  const isSearching = searchQuery.length >= 2;
  const isLoading = isSearching ? isSearchLoading : isListLoading;
  const error = isSearching ? searchError : listError;
  const total = isSearching ? (searchData?.length || 0) : (listData?.total || 0);

  // Client-side sorting
  const sortedPlayers = useMemo(() => {
    const players = isSearching ? searchData : listData?.players;
    if (!players) return [];

    return [...players].sort((a: ExtendedPlayer, b: ExtendedPlayer) => {
      const aValue = a[sortField];
      const bValue = b[sortField];

      if (aValue === undefined || bValue === undefined) return 0;
      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [isSearching, searchData, listData, sortField, sortDirection]);

  // Filter handlers
  const updateFilter = useCallback((key: keyof PlayerFilters, value: string | number | undefined) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(0); // Reset to first page when filters change
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({});
    setSearchQuery('');
    setPage(0);
  }, []);

  // Sort handler
  const toggleSort = useCallback((field: PlayerSortField) => {
    setSortField((prev) => {
      if (prev === field) {
        setSortDirection((dir) => (dir === 'asc' ? 'desc' : 'asc'));
        return prev;
      }
      setSortDirection('desc');
      return field;
    });
  }, []);

  // Pagination handlers
  const nextPage = useCallback(() => {
    if (!isSearching && hasNextPage) {
      setPage((p) => p + 1);
    }
  }, [isSearching, hasNextPage]);

  const prevPage = useCallback(() => {
    setPage((p) => Math.max(0, p - 1));
  }, []);

  const goToPage = useCallback((newPage: number) => {
    setPage(Math.max(0, newPage));
  }, []);

  return {
    // Data
    players: sortedPlayers,
    total,
    isLoading,
    error,

    // Filters
    filters,
    searchQuery,
    setSearchQuery,
    updateFilter,
    clearFilters,

    // Sorting
    sortField,
    sortDirection,
    toggleSort,

    // Pagination
    page,
    pageSize,
    totalPages: Math.ceil(total / pageSize),
    nextPage,
    prevPage,
    goToPage,
    hasNextPage: isSearching ? false : hasNextPage,
    isFetchingNextPage,
    fetchNextPage,

    // State
    isSearching,
  };
}

// Hook for comparing multiple players
export function usePlayerComparison(playerIds: string[]) {
  // This would fetch multiple players and prepare comparison data
  // For now, it's a placeholder for future implementation
  
  return {
    comparedPlayers: [],
    isLoading: false,
    error: null,
  };
}

// Hook for player statistics over time
export function usePlayerTrends(playerId: string, timeframe: '7d' | '30d' | '90d' | 'all' = '30d') {
  // This would fetch historical data for trend analysis
  // For now, it's a placeholder for future implementation
  
  return {
    trends: [],
    isLoading: false,
    error: null,
  };
}
