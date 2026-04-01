import { Link } from 'react-router-dom';
import { MapPin, Clock, Users } from 'lucide-react';
import type { ExtendedMatch } from '../../types';

interface MatchCardProps {
  match: ExtendedMatch;
  compact?: boolean;
}

export function MatchCard({ match, compact = false }: MatchCardProps) {
  const isLive = match.status === 'live';
  const isUpcoming = match.status === 'upcoming';

  if (compact) {
    return (
      <Link
        to={`/matches/${match.id}`}
        className="flex items-center gap-4 p-3 bg-radiant-card rounded-lg border border-radiant-border hover:border-radiant-red/30 transition-all"
      >
        <div className="flex items-center gap-2">
          {isLive && <div className="w-2 h-2 bg-radiant-red rounded-full live-dot" />}
          <span className="text-sm font-medium">
            {match.teamA?.name || 'TBD'} vs {match.teamB?.name || 'TBD'}
          </span>
        </div>
        <div className="flex-1" />
        <span className="text-xs text-radiant-gray">{match.mapName}</span>
      </Link>
    );
  }

  return (
    <Link
      to={`/matches/${match.id}`}
      className="stat-card p-6 block hover:border-radiant-red/30 transition-all group"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {isLive && (
            <>
              <div className="w-2 h-2 bg-radiant-red rounded-full live-dot" />
              <span className="text-xs font-medium text-radiant-red uppercase">Live</span>
            </>
          )}
          {isUpcoming && (
            <>
              <div className="w-2 h-2 bg-radiant-orange rounded-full animate-pulse" />
              <span className="text-xs font-medium text-radiant-orange uppercase">Upcoming</span>
            </>
          )}
          {!isLive && !isUpcoming && (
            <span className="text-xs font-medium text-radiant-green uppercase">Finished</span>
          )}
        </div>
        <span className="text-xs text-radiant-gray">{match.tournament || 'VCT'}</span>
      </div>

      {/* Teams */}
      <div className="flex items-center justify-center gap-8 mb-4">
        <div className="text-center">
          <p className="text-2xl font-bold group-hover:text-radiant-cyan transition-colors">
            {match.teamA?.name || 'TBD'}
          </p>
          <p className="text-sm text-radiant-gray">{match.teamA?.score ?? '-'}</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-mono text-radiant-gray">VS</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold group-hover:text-radiant-cyan transition-colors">
            {match.teamB?.name || 'TBD'}
          </p>
          <p className="text-sm text-radiant-gray">{match.teamB?.score ?? '-'}</p>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-radiant-border text-sm text-radiant-gray">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <MapPin className="w-4 h-4" />
            {match.mapName}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            {match.roundsPlayed} rounds
          </span>
        </div>
        <span className="flex items-center gap-1">
          <Users className="w-4 h-4" />
          {match.playerIds.length} players
        </span>
      </div>
    </Link>
  );
}
