import { Trophy, Calendar, Filter, MapPin } from 'lucide-react';
import { useState } from 'react';
import { useMatches } from '../hooks/useApi';
import { MatchList } from '../components/Matches/MatchList';
import type { MatchFilters } from '../types';

const maps = ['Haven', 'Ascent', 'Bind', 'Split', 'Icebox', 'Breeze', 'Fracture', 'Pearl', 'Lotus', 'Sunset'];
const tournaments = ['VCT Masters', 'VCT Americas', 'VCT EMEA', 'VCT Pacific', 'Champions'];

export function MatchesPage() {
  const [filters, setFilters] = useState<MatchFilters>({});
  const [activeTab, setActiveTab] = useState<'all' | 'live' | 'upcoming' | 'finished'>('all');

  const { data: matches, isLoading } = useMatches(filters);

  const handleTabChange = (tab: typeof activeTab) => {
    setActiveTab(tab);
    if (tab === 'all') {
      setFilters((prev) => ({ ...prev, status: undefined }));
    } else {
      setFilters((prev) => ({ ...prev, status: tab }));
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Matches</h1>
        <p className="text-radiant-gray mt-1">
          View match history, live games, and upcoming fixtures
        </p>
      </div>

      {/* Status Tabs */}
      <div className="flex flex-wrap gap-2">
        {(['all', 'live', 'upcoming', 'finished'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => handleTabChange(tab)}
            className={`px-4 py-2 text-sm font-medium rounded-lg capitalize transition-all ${
              activeTab === tab
                ? 'bg-radiant-red text-white'
                : 'bg-radiant-card text-radiant-gray hover:text-white border border-radiant-border'
            }`}
          >
            {tab === 'live' && (
              <span className="inline-flex items-center gap-2">
                <span className="w-2 h-2 bg-white rounded-full live-dot" />
                Live
              </span>
            )}
            {tab !== 'live' && tab}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 text-sm text-radiant-gray">
          <Filter className="w-4 h-4" />
          Filters:
        </div>

        <select
          value={filters.map || ''}
          onChange={(e) =>
            setFilters((prev) => ({ ...prev, map: e.target.value || undefined }))
          }
          className="input-field w-auto text-sm py-2"
        >
          <option value="">All Maps</option>
          {maps.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>

        <select
          value={filters.tournament || ''}
          onChange={(e) =>
            setFilters((prev) => ({
              ...prev,
              tournament: e.target.value || undefined,
            }))
          }
          className="input-field w-auto text-sm py-2"
        >
          <option value="">All Tournaments</option>
          {tournaments.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      {/* Match List */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-radiant-gray">
            {isLoading
              ? 'Loading matches...'
              : `${matches?.length || 0} matches found`}
          </p>
        </div>
        <MatchList matches={matches || []} isLoading={isLoading} />
      </div>
    </div>
  );
}
