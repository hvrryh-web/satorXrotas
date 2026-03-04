import { BarChart3, Target, TrendingUp, Award, Info } from 'lucide-react';
import { useState } from 'react';
import { usePlayers, useSimRating, useRAR } from '../hooks/useApi';
import { SimRatingChart } from '../components/Analytics/SimRatingChart';

export function AnalyticsPage() {
  const [selectedPlayerId, setSelectedPlayerId] = useState<string>('');
  const { data: players } = usePlayers({}, 0, 20);
  const { data: simRating } = useSimRating(selectedPlayerId, undefined, {
    enabled: !!selectedPlayerId,
  });
  const { data: rar } = useRAR(selectedPlayerId, {
    enabled: !!selectedPlayerId,
  });

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Analytics</h1>
        <p className="text-radiant-gray mt-1">
          Advanced metrics and predictive insights powered by SATOR
        </p>
      </div>

      {/* Metrics Overview */}
      <div className="grid md:grid-cols-3 gap-6">
        <MetricCard
          icon={Target}
          title="SimRating"
          description="Composite performance score based on z-scores across key metrics including kills, deaths, ADR, and KAST%."
          color="cyan"
        />
        <MetricCard
          icon={TrendingUp}
          title="RAR Score"
          description="Role-Adjusted value above Replacement. Compares player performance to replacement-level baseline for their role."
          color="gold"
        />
        <MetricCard
          icon={Award}
          title="Investment Grade"
          description="Letter grade (A+ to D) indicating player value for fantasy/investment purposes based on performance and age curve."
          color="green"
        />
      </div>

      {/* Player Selector */}
      <div className="stat-card p-6">
        <label className="block text-sm font-medium mb-3">Select Player for Analysis</label>
        <select
          value={selectedPlayerId}
          onChange={(e) => setSelectedPlayerId(e.target.value)}
          className="input-field"
        >
          <option value="">Choose a player...</option>
          {players?.players.map((player) => (
            <option key={player.player_id} value={player.player_id}>
              {player.name} {player.team ? `(${player.team})` : ''} - Rating:{' '}
              {player.sim_rating?.toFixed(2) || 'N/A'}
            </option>
          ))}
        </select>
      </div>

      {/* Analytics Display */}
      {selectedPlayerId && (
        <div className="grid lg:grid-cols-2 gap-6">
          {/* SimRating */}
          <div className="stat-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Target className="w-5 h-5 text-radiant-cyan" />
              <h2 className="text-lg font-semibold">SimRating Analysis</h2>
            </div>
            {simRating ? (
              <SimRatingChart data={simRating} />
            ) : (
              <div className="h-64 flex items-center justify-center text-radiant-gray">
                Loading SimRating data...
              </div>
            )}
          </div>

          {/* RAR Analysis */}
          <div className="stat-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-5 h-5 text-radiant-gold" />
              <h2 className="text-lg font-semibold">RAR Analysis</h2>
            </div>
            {rar ? (
              <div className="space-y-4">
                <div className="p-6 bg-radiant-black rounded-lg text-center">
                  <p className="text-sm text-radiant-gray mb-2">RAR Score</p>
                  <p className="text-5xl font-mono font-bold text-radiant-gold">
                    {rar.rar_score.toFixed(2)}
                  </p>
                  <p className="text-sm text-radiant-gray mt-2">
                    Value above replacement level
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-radiant-black rounded-lg">
                    <p className="text-sm text-radiant-gray">Raw Rating</p>
                    <p className="text-xl font-mono font-semibold">
                      {rar.raw_rating.toFixed(2)}
                    </p>
                  </div>
                  <div className="p-4 bg-radiant-black rounded-lg">
                    <p className="text-sm text-radiant-gray">Replacement Level</p>
                    <p className="text-xl font-mono font-semibold">
                      {rar.replacement_level.toFixed(2)}
                    </p>
                  </div>
                </div>
                <div className="p-4 bg-radiant-black rounded-lg">
                  <p className="text-sm text-radiant-gray">Role</p>
                  <p className="text-lg font-medium">{rar.role}</p>
                </div>
                {rar.investment_grade && (
                  <div className="p-4 bg-radiant-black rounded-lg flex items-center justify-between">
                    <span className="text-radiant-gray">Investment Grade</span>
                    <span
                      className={`text-2xl font-bold ${
                        rar.investment_grade === 'A+'
                          ? 'text-radiant-gold'
                          : rar.investment_grade === 'A'
                          ? 'text-radiant-cyan'
                          : rar.investment_grade === 'B'
                          ? 'text-radiant-green'
                          : 'text-radiant-gray'
                      }`}
                    >
                      {rar.investment_grade}
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-radiant-gray">
                Loading RAR data...
              </div>
            )}
          </div>
        </div>
      )}

      {/* Methodology Info */}
      <div className="stat-card p-6">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-radiant-cyan shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold mb-2">About SATOR Analytics</h3>
            <p className="text-sm text-radiant-gray leading-relaxed">
              SATOR (Simulation Analytics for Tactical Operations Research) is a multi-layered
              analytics engine designed for esports performance evaluation. The system uses
              z-score normalization across key performance indicators to create standardized
              ratings that account for role differences and meta variations.
            </p>
            <div className="mt-4 grid md:grid-cols-2 gap-4 text-sm">
              <div>
                <h4 className="font-medium text-radiant-cyan mb-1">SimRating Formula</h4>
                <p className="text-radiant-gray">
                  Weighted composite of normalized kills, deaths, adjusted kill value, ADR, and
                  KAST percentage.
                </p>
              </div>
              <div>
                <h4 className="font-medium text-radiant-gold mb-1">RAR Calculation</h4>
                <p className="text-radiant-gray">
                  Raw SimRating minus role-specific replacement level, accounting for position
                  scarcity and baseline performance.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface MetricCardProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  color: 'cyan' | 'gold' | 'green';
}

function MetricCard({ icon: Icon, title, description, color }: MetricCardProps) {
  const colorClasses = {
    cyan: 'text-radiant-cyan bg-radiant-cyan/10 border-radiant-cyan/30',
    gold: 'text-radiant-gold bg-radiant-gold/10 border-radiant-gold/30',
    green: 'text-radiant-green bg-radiant-green/10 border-radiant-green/30',
  };

  return (
    <div className={`stat-card p-6 border ${colorClasses[color]}`}>
      <div className="flex items-center gap-3 mb-3">
        <Icon className="w-6 h-6" />
        <h3 className="text-lg font-semibold">{title}</h3>
      </div>
      <p className="text-sm text-radiant-gray leading-relaxed">{description}</p>
    </div>
  );
}
