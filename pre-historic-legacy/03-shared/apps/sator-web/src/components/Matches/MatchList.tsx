import { Calendar, MapPin, Clock, Trophy } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { ExtendedMatch } from '../../types';

interface MatchListProps {
  matches: ExtendedMatch[];
  isLoading: boolean;
}

export function MatchList({ matches, isLoading }: MatchListProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-32 skeleton" />
        ))}
      </div>
    );
  }

  if (matches.length === 0) {
    return (
      <div className="bg-radiant-card rounded-xl border border-radiant-border p-12 text-center">
        <p className="text-radiant-gray text-lg">No matches found</p>
        <p className="text-sm text-radiant-gray/60 mt-2">
          Try adjusting your filters
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {matches.map((match) => (
        <MatchCard key={match.id} match={match} />
      ))}
    </div>
  );
}

function MatchCard({ match }: { match: ExtendedMatch }) {
  const isLive = match.status === 'live';
  const isUpcoming = match.status === 'upcoming';
  const isFinished = match.status === 'finished';

  return (
    <Link
      to={`/matches/${match.id}`}
      className="stat-card p-6 block hover:border-radiant-red/30 transition-all group"
    >
      <div className="flex flex-col md:flex-row md:items-center gap-4">
        {/* Status & Tournament */}
        <div className="flex items-center gap-4 md:w-48 shrink-0">
          <div className="flex items-center gap-2">
            {isLive && (
              <>
                <div className="w-2 h-2 bg-radiant-red rounded-full live-dot" />
                <span className="text-xs font-medium text-radiant-red uppercase">Live</span>
              </>
            )}
            {isFinished && (
              <>
                <div className="w-2 h-2 bg-radiant-green rounded-full" />
                <span className="text-xs font-medium text-radiant-green uppercase">Finished</span>
              </>
            )}
            {isUpcoming && (
              <>
                <div className="w-2 h-2 bg-radiant-orange rounded-full animate-pulse" />
                <span className="text-xs font-medium text-radiant-orange uppercase">Upcoming</span>
              </>
            )}
          </div>
          <span className="text-xs text-radiant-gray">{match.tournament || 'VCT'}</span>
        </div>

        {/* Teams & Score */}
        <div className="flex-1 flex items-center justify-center gap-6">
          <div className="text-center">
            <p className="text-xl font-bold">{match.teamA?.name || 'TBD'}</p>
            <p className="text-xs text-radiant-gray">
              {match.teamA?.players.length || 0} players
            </p>
          </div>
          <div className="text-center px-4">
            {isUpcoming ? (
              <p className="text-xl font-bold font-mono">VS</p>
            ) : (
              <p className="text-2xl font-bold font-mono">
                {match.teamA?.score || 0} - {match.teamB?.score || 0}
              </p>
            )}
            <p className="text-xs text-radiant-gray">
              {isUpcoming ? 'TBD' : `${match.roundsPlayed} rounds`}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xl font-bold">{match.teamB?.name || 'TBD'}</p>
            <p className="text-xs text-radiant-gray">
              {match.teamB?.players.length || 0} players
            </p>
          </div>
        </div>

        {/* Map & Time */}
        <div className="md:w-48 shrink-0 flex md:flex-col items-center md:items-end gap-4 md:gap-1 text-sm text-radiant-gray">
          <div className="flex items-center gap-1">
            <MapPin className="w-4 h-4" />
            {match.mapName}
          </div>
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            {formatMatchTime(match)}
          </div>
        </div>
      </div>
    </Link>
  );
}

function formatMatchTime(match: ExtendedMatch): string {
  if (match.status === 'live') {
    return 'In Progress';
  }
  if (match.status === 'upcoming') {
    const start = new Date(match.startedAt);
    const now = new Date();
    const diff = start.getTime() - now.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    if (hours < 1) {
      const minutes = Math.floor(diff / (1000 * 60));
      return `In ${minutes}m`;
    }
    return `In ${hours}h`;
  }
  return new Date(match.endedAt).toLocaleDateString();
}
