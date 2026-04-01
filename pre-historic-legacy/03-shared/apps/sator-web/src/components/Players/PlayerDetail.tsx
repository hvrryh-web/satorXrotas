import { Link } from 'react-router-dom';
import { ArrowLeft, Users, MapPin, Calendar, TrendingUp, Target, Award } from 'lucide-react';
import type { ExtendedPlayer, SimRatingBreakdown, RARResponse } from '../../types';
import { SimRatingChart } from '../Analytics/SimRatingChart';
import { StatsTable } from '../Analytics/StatsTable';

interface PlayerDetailProps {
  player: ExtendedPlayer;
  simRating?: SimRatingBreakdown;
  rar?: RARResponse;
  isLoadingAnalytics?: boolean;
}

export function PlayerDetail({
  player,
  simRating,
  rar,
  isLoadingAnalytics = false,
}: PlayerDetailProps) {
  return (
    <div className="space-y-6">
      {/* Back Navigation */}
      <Link
        to="/players"
        className="inline-flex items-center gap-2 text-sm text-radiant-gray hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Players
      </Link>

      {/* Player Header */}
      <div className="stat-card p-6">
        <div className="flex flex-col md:flex-row md:items-center gap-6">
          <div className="w-24 h-24 rounded-full bg-gradient-to-br from-radiant-red to-radiant-orange flex items-center justify-center text-3xl font-bold">
            {player.name.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold">{player.name}</h1>
              {player.investment_grade && (
                <span
                  className={`inline-flex items-center px-3 py-1 text-sm font-bold rounded ${
                    player.investment_grade === 'A+'
                      ? 'bg-radiant-gold/20 text-radiant-gold'
                      : player.investment_grade === 'A'
                      ? 'bg-radiant-cyan/20 text-radiant-cyan'
                      : player.investment_grade === 'B'
                      ? 'bg-radiant-green/20 text-radiant-green'
                      : 'bg-radiant-gray/20 text-radiant-gray'
                  }`}
                >
                  Grade {player.investment_grade}
                </span>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-4 text-sm text-radiant-gray">
              {player.team && (
                <span className="flex items-center gap-1">
                  <Users className="w-4 h-4" />
                  {player.team}
                </span>
              )}
              {player.region && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-4 h-4" />
                  {player.region}
                </span>
              )}
              {player.role && (
                <span className="flex items-center gap-1">
                  <Award className="w-4 h-4" />
                  {player.role}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Key Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="ACS"
          value={player.acs?.toFixed(1) || '-'}
          icon={Target}
          color="cyan"
        />
        <StatCard
          label="ADR"
          value={player.adr?.toFixed(1) || '-'}
          icon={TrendingUp}
          color="red"
        />
        <StatCard
          label="KAST%"
          value={player.kast_pct ? `${player.kast_pct.toFixed(1)}%` : '-'}
          icon={Calendar}
          color="gold"
        />
        <StatCard
          label="Maps"
          value={player.map_count?.toString() || '-'}
          icon={MapPin}
          color="green"
        />
      </div>

      {/* Analytics Section */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* SimRating Chart */}
        <div className="stat-card p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-radiant-cyan" />
            SimRating Breakdown
          </h2>
          {isLoadingAnalytics ? (
            <div className="h-64 skeleton" />
          ) : simRating ? (
            <SimRatingChart data={simRating} />
          ) : (
            <p className="text-radiant-gray text-center py-8">
              No SimRating data available
            </p>
          )}
        </div>

        {/* RAR Score */}
        <div className="stat-card p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-radiant-gold" />
            Role-Adjusted Value
          </h2>
          {isLoadingAnalytics ? (
            <div className="h-64 skeleton" />
          ) : rar ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-radiant-black rounded-lg">
                <span className="text-radiant-gray">RAR Score</span>
                <span className="text-2xl font-mono font-bold text-radiant-gold">
                  {rar.rar_score.toFixed(2)}
                </span>
              </div>
              <div className="flex items-center justify-between p-4 bg-radiant-black rounded-lg">
                <span className="text-radiant-gray">Raw Rating</span>
                <span className="font-mono">{rar.raw_rating.toFixed(2)}</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-radiant-black rounded-lg">
                <span className="text-radiant-gray">Replacement Level</span>
                <span className="font-mono">{rar.replacement_level.toFixed(2)}</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-radiant-black rounded-lg">
                <span className="text-radiant-gray">Role</span>
                <span className="font-medium">{rar.role}</span>
              </div>
            </div>
          ) : (
            <p className="text-radiant-gray text-center py-8">
              No RAR data available
            </p>
          )}
        </div>
      </div>

      {/* Detailed Stats Table */}
      <div className="stat-card p-6">
        <h2 className="text-lg font-semibold mb-4">Performance Statistics</h2>
        <StatsTable player={player} />
      </div>
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color: 'cyan' | 'red' | 'gold' | 'green';
}

function StatCard({ label, value, icon: Icon, color }: StatCardProps) {
  const colorClasses = {
    cyan: 'text-radiant-cyan bg-radiant-cyan/10',
    red: 'text-radiant-red bg-radiant-red/10',
    gold: 'text-radiant-gold bg-radiant-gold/10',
    green: 'text-radiant-green bg-radiant-green/10',
  };

  return (
    <div className="stat-card p-4">
      <div className="flex items-center gap-3 mb-2">
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-4 h-4" />
        </div>
        <span className="text-sm text-radiant-gray">{label}</span>
      </div>
      <p className="text-2xl font-mono font-bold">{value}</p>
    </div>
  );
}
