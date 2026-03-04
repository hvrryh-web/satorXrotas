import { Search, Filter, X, MapPin, Users, Award } from 'lucide-react';
import { PlayerList } from '../components/Players/PlayerList';
import { usePlayerList } from '../hooks/usePlayers';

const regions = ['NA', 'EU', 'APAC', 'BR', 'KR', 'JP', 'LATAM'];
const roles = ['Duelist', 'Controller', 'Initiator', 'Sentinel', 'Flex'];
const grades = ['A+', 'A', 'B', 'C', 'D'];

export function PlayersPage() {
  const {
    players,
    isLoading,
    sortField,
    sortDirection,
    toggleSort,
    page,
    totalPages,
    goToPage,
    filters,
    updateFilter,
    searchQuery,
    setSearchQuery,
    clearFilters,
    isSearching,
  } = usePlayerList({}, 50);

  const hasActiveFilters =
    filters.region || filters.role || filters.grade || searchQuery;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Players</h1>
          <p className="text-radiant-gray mt-1">
            Browse and analyze player performance metrics
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-radiant-gray">Min Maps:</span>
          <select
            value={filters.minMaps || 50}
            onChange={(e) => updateFilter('minMaps', parseInt(e.target.value))}
            className="input-field w-auto"
          >
            <option value={10}>10+</option>
            <option value={25}>25+</option>
            <option value={50}>50+</option>
            <option value={100}>100+</option>
          </select>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="space-y-4">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-radiant-gray" />
          <input
            type="text"
            placeholder="Search players or teams..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-field pl-12 pr-4 py-3"
            id="global-search"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-radiant-gray hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 text-sm text-radiant-gray">
            <Filter className="w-4 h-4" />
            Filters:
          </div>

          {/* Region Filter */}
          <select
            value={filters.region || ''}
            onChange={(e) => updateFilter('region', e.target.value || undefined)}
            className="input-field w-auto text-sm py-2"
          >
            <option value="">All Regions</option>
            {regions.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>

          {/* Role Filter */}
          <select
            value={filters.role || ''}
            onChange={(e) => updateFilter('role', e.target.value || undefined)}
            className="input-field w-auto text-sm py-2"
          >
            <option value="">All Roles</option>
            {roles.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>

          {/* Grade Filter */}
          <select
            value={filters.grade || ''}
            onChange={(e) => updateFilter('grade', e.target.value || undefined)}
            className="input-field w-auto text-sm py-2"
          >
            <option value="">All Grades</option>
            {grades.map((g) => (
              <option key={g} value={g}>
                Grade {g}
              </option>
            ))}
          </select>

          {/* Clear Filters */}
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="text-sm text-radiant-red hover:text-radiant-red/80 flex items-center gap-1 transition-colors"
            >
              <X className="w-3 h-3" />
              Clear
            </button>
          )}
        </div>

        {/* Active Filter Tags */}
        {hasActiveFilters && (
          <div className="flex flex-wrap items-center gap-2">
            {filters.region && (
              <FilterTag
                icon={MapPin}
                label={filters.region}
                onRemove={() => updateFilter('region', undefined)}
              />
            )}
            {filters.role && (
              <FilterTag
                icon={Users}
                label={filters.role}
                onRemove={() => updateFilter('role', undefined)}
              />
            )}
            {filters.grade && (
              <FilterTag
                icon={Award}
                label={`Grade ${filters.grade}`}
                onRemove={() => updateFilter('grade', undefined)}
              />
            )}
            {searchQuery && (
              <FilterTag
                icon={Search}
                label={`Search: ${searchQuery}`}
                onRemove={() => setSearchQuery('')}
              />
            )}
          </div>
        )}
      </div>

      {/* Results */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-radiant-gray">
            {isLoading ? 'Loading...' : `Showing ${players.length} players`}
            {isSearching && ' (search results)'}
          </p>
        </div>

        <PlayerList
          players={players}
          isLoading={isLoading}
          sortField={sortField}
          sortDirection={sortDirection}
          onSort={toggleSort}
          page={page}
          totalPages={totalPages}
          onPageChange={goToPage}
        />
      </div>
    </div>
  );
}

interface FilterTagProps {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  onRemove: () => void;
}

function FilterTag({ icon: Icon, label, onRemove }: FilterTagProps) {
  return (
    <span className="inline-flex items-center gap-1 px-3 py-1 bg-radiant-card border border-radiant-border rounded-full text-sm">
      <Icon className="w-3 h-3 text-radiant-gray" />
      {label}
      <button
        onClick={onRemove}
        className="ml-1 text-radiant-gray hover:text-radiant-red transition-colors"
      >
        <X className="w-3 h-3" />
      </button>
    </span>
  );
}
