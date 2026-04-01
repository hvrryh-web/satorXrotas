import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, MapPin, Clock, Users, Trophy } from 'lucide-react';
import { useMatch } from '../hooks/useApi';
import { AlertTriangle, Loader2 } from 'lucide-react';

export function MatchDetailPage() {
  const { id } = useParams<{ id: string }>();

  const {
    data: match,
    isLoading,
    error,
  } = useMatch(id || '', {
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="flex items-center gap-3 text-radiant-gray">
          <Loader2 className="w-6 h-6 animate-spin" />
          <span>Loading match data...</span>
        </div>
      </div>
    );
  }

  if (error || !match) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-radiant-red/10 rounded-full flex items-center justify-center">
            <AlertTriangle className="w-8 h-8 text-radiant-red" />
          </div>
          <h2 className="text-xl font-bold mb-2">Match Not Found</h2>
          <p className="text-radiant-gray">
            The match you are looking for does not exist or has been removed.
          </p>
        </div>
      </div>
    );
  }

  const isLive = match.status === 'live';
  const isUpcoming = match.status === 'upcoming';

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back Navigation */}
      <Link
        to="/matches"
        className="inline-flex items-center gap-2 text-sm text-radiant-gray hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Matches
      </Link>

      {/* Match Header */}
      <div className="stat-card p-8">
        {/* Status & Tournament */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            {isLive && (
              <>
                <div className="w-3 h-3 bg-radiant-red rounded-full live-dot" />
                <span className="text-sm font-medium text-radiant-red uppercase">Live</span>
              </>
            )}
            {isUpcoming && (
              <span className="text-sm font-medium text-radiant-orange uppercase">Upcoming</span>
            )}
            {!isLive && !isUpcoming && (
              <span className="text-sm font-medium text-radiant-green uppercase">Finished</span>
            )}
          </div>
          <div className="flex items-center gap-2 text-radiant-gray">
            <Trophy className="w-4 h-4" />
            {match.tournament || 'VCT'}
          </div>
        </div>

        {/* Teams & Score */}
        <div className="flex items-center justify-center gap-8 md:gap-16 mb-8">
          <div className="text-center">
            <p className="text-3xl md:text-5xl font-bold mb-2">
              {match.teamA?.name || 'TBD'}
            </p>
            <p className="text-4xl md:text-6xl font-mono font-bold text-radiant-cyan">
              {match.teamA?.score ?? '-'}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xl md:text-2xl font-bold text-radiant-gray">VS</p>
          </div>
          <div className="text-center">
            <p className="text-3xl md:text-5xl font-bold mb-2">
              {match.teamB?.name || 'TBD'}
            </p>
            <p className="text-4xl md:text-6xl font-mono font-bold text-radiant-cyan">
              {match.teamB?.score ?? '-'}
            </p>
          </div>
        </div>

        {/* Match Info */}
        <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-radiant-gray pt-6 border-t border-radiant-border">
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4" />
            {match.mapName}
          </div>
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4" />
            {match.roundsPlayed} rounds
          </div>
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            {match.playerIds.length} players
          </div>
        </div>
      </div>

      {/* Match Details */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Team A Players */}
        <div className="stat-card p-6">
          <h2 className="text-lg font-semibold mb-4">{match.teamA?.name || 'Team A'}</h2>
          <div className="space-y-2">
            {match.teamA?.players.map((playerId) => (
              <PlayerRow key={playerId} playerId={playerId} />
            )) || <p className="text-radiant-gray">No player data available</p>}
          </div>
        </div>

        {/* Team B Players */}
        <div className="stat-card p-6">
          <h2 className="text-lg font-semibold mb-4">{match.teamB?.name || 'Team B'}</h2>
          <div className="space-y-2">
            {match.teamB?.players.map((playerId) => (
              <PlayerRow key={playerId} playerId={playerId} />
            )) || <p className="text-radiant-gray">No player data available</p>}
          </div>
        </div>
      </div>
    </div>
  );
}

function PlayerRow({ playerId }: { playerId: string }) {
  // This would fetch player details - for now just show ID
  return (
    <div className="flex items-center justify-between p-3 bg-radiant-black rounded-lg">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-radiant-card border border-radiant-border flex items-center justify-center text-sm font-bold">
          {playerId.charAt(0).toUpperCase()}
        </div>
        <span className="font-medium">Player {playerId.slice(0, 8)}</span>
      </div>
      <Link
        to={`/players/${playerId}`}
        className="text-sm text-radiant-cyan hover:text-radiant-cyan/80 transition-colors"
      >
        View Profile
      </Link>
    </div>
  );
}
