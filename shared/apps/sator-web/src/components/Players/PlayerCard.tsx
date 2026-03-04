import { Link } from 'react-router-dom';
import { Users, MapPin, TrendingUp, Award } from 'lucide-react';
import type { ExtendedPlayer } from '../../types';

interface PlayerCardProps {
  player: ExtendedPlayer;
  showStats?: boolean;
}

export function PlayerCard({ player, showStats = true }: PlayerCardProps) {
  return (
    <Link
      to={`/players/${player.player_id}`}
      className="stat-card p-4 block hover:border-radiant-red/30 transition-all group"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-radiant-red/20 to-radiant-orange/20 border border-radiant-border flex items-center justify-center">
            <span className="font-bold text-lg">
              {player.name.charAt(0).toUpperCase()}
            </span>
          </div>
          <div>
            <h3 className="font-semibold group-hover:text-radiant-cyan transition-colors">
              {player.name}
            </h3>
            <div className="flex items-center gap-2 text-xs text-radiant-gray">
              {player.team && (
                <span className="flex items-center gap-1">
                  <Users className="w-3 h-3" />
                  {player.team}
                </span>
              )}
              {player.region && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {player.region}
                </span>
              )}
            </div>
          </div>
        </div>
        {player.investment_grade && (
          <span
            className={`inline-flex items-center px-2 py-1 text-xs font-bold rounded ${
              player.investment_grade === 'A+'
                ? 'bg-radiant-gold/20 text-radiant-gold'
                : player.investment_grade === 'A'
                ? 'bg-radiant-cyan/20 text-radiant-cyan'
                : player.investment_grade === 'B'
                ? 'bg-radiant-green/20 text-radiant-green'
                : 'bg-radiant-gray/20 text-radiant-gray'
            }`}
          >
            {player.investment_grade}
          </span>
        )}
      </div>

      {showStats && (
        <div className="grid grid-cols-3 gap-4 pt-4 border-t border-radiant-border">
          <div className="text-center">
            <p className="text-lg font-mono font-semibold">
              {player.acs?.toFixed(0) || '-'}
            </p>
            <p className="text-xs text-radiant-gray">ACS</p>
          </div>
          <div className="text-center">
            <p className="text-lg font-mono font-semibold">
              {player.sim_rating?.toFixed(2) || '-'}
            </p>
            <p className="text-xs text-radiant-gray">Rating</p>
          </div>
          <div className="text-center">
            <p className="text-lg font-mono font-semibold">
              {player.map_count || '-'}
            </p>
            <p className="text-xs text-radiant-gray">Maps</p>
          </div>
        </div>
      )}

      {player.role && (
        <div className="mt-4 flex items-center gap-2">
          <Award className="w-4 h-4 text-radiant-gray" />
          <span className="text-sm text-radiant-gray">{player.role}</span>
        </div>
      )}
    </Link>
  );
}
