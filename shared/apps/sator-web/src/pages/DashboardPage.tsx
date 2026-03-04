import { Trophy, Users, Target, TrendingUp, ArrowRight, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useDashboardStats, usePlayers, useMatches } from '../hooks/useApi';
import { PlayerCard } from '../components/Players/PlayerCard';
import { MatchCard } from '../components/Matches/MatchCard';
import { SatorSphere } from '../components/SatorSphere';

export function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: topPlayers, isLoading: playersLoading } = usePlayers({}, 0, 4);
  const { data: liveMatches, isLoading: matchesLoading } = useMatches({ status: 'live' });

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-radiant-card to-radiant-black border border-radiant-border p-8">
        <div className="relative z-10">
          <div className="flex flex-col lg:flex-row items-center gap-8">
            <div className="flex-1 text-center lg:text-left">
              <p className="text-radiant-cyan text-sm font-mono tracking-widest uppercase mb-4">
                SATOR Analytics Platform
              </p>
              <h1 className="text-4xl sm:text-5xl font-bold leading-tight mb-6">
                Decode the{' '}
                <span className="text-gradient">Game</span>
              </h1>
              <p className="text-radiant-gray text-lg mb-8 max-w-lg mx-auto lg:mx-0">
                Advanced analytics for Valorant and CS. Real-time match data, player performance metrics, and predictive insights powered by the SATOR engine.
              </p>
              <div className="flex flex-wrap gap-4 justify-center lg:justify-start">
                <Link to="/matches" className="btn-primary inline-flex items-center gap-2">
                  <Trophy className="w-4 h-4" />
                  View Matches
                </Link>
                <Link to="/players" className="btn-secondary inline-flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  Explore Players
                </Link>
              </div>
            </div>
            <div className="w-full max-w-[300px] lg:max-w-[400px]">
              <SatorSphere />
            </div>
          </div>
        </div>
        
        {/* Background decoration */}
        <div className="absolute inset-0 bg-gradient-to-br from-radiant-red/5 via-transparent to-radiant-cyan/5 pointer-events-none" />
      </section>

      {/* Stats Overview */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Matches"
          value={statsLoading ? '-' : formatNumber(stats?.totalMatches || 0)}
          icon={Trophy}
          color="red"
        />
        <StatCard
          label="Players Tracked"
          value={statsLoading ? '-' : formatNumber(stats?.totalPlayers || 0)}
          icon={Users}
          color="cyan"
        />
        <StatCard
          label="Tournaments"
          value={statsLoading ? '-' : stats?.totalTournaments.toString() || '-'}
          icon={Target}
          color="gold"
        />
        <StatCard
          label="Live Matches"
          value={statsLoading ? '-' : stats?.liveMatches.toString() || '0'}
          icon={Zap}
          color="green"
          pulse
        />
      </section>

      {/* Live Matches */}
      {liveMatches && liveMatches.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <div className="w-2 h-2 bg-radiant-red rounded-full live-dot" />
              Live Matches
            </h2>
            <Link
              to="/matches"
              className="text-sm text-radiant-cyan hover:text-radiant-cyan/80 transition-colors flex items-center gap-1"
            >
              View All
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {matchesLoading
              ? [...Array(3)].map((_, i) => <div key={i} className="h-48 skeleton" />)
              : liveMatches.slice(0, 3).map((match) => <MatchCard key={match.id} match={match} />)}
          </div>
        </section>
      )}

      {/* Top Players */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-radiant-gold" />
            Top Performers
          </h2>
          <Link
            to="/players"
            className="text-sm text-radiant-cyan hover:text-radiant-cyan/80 transition-colors flex items-center gap-1"
          >
            View All
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          {playersLoading
            ? [...Array(4)].map((_, i) => <div key={i} className="h-48 skeleton" />)
            : topPlayers?.players.map((player) => <PlayerCard key={player.player_id} player={player} />)}
        </div>
      </section>
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color: 'cyan' | 'red' | 'gold' | 'green';
  pulse?: boolean;
}

function StatCard({ label, value, icon: Icon, color, pulse }: StatCardProps) {
  const colorClasses = {
    cyan: 'text-radiant-cyan bg-radiant-cyan/10 border-radiant-cyan/30',
    red: 'text-radiant-red bg-radiant-red/10 border-radiant-red/30',
    gold: 'text-radiant-gold bg-radiant-gold/10 border-radiant-gold/30',
    green: 'text-radiant-green bg-radiant-green/10 border-radiant-green/30',
  };

  return (
    <div className={`stat-card p-6 border ${colorClasses[color]}`}>
      <div className="flex items-center gap-3 mb-2">
        <div className={`p-2 rounded-lg bg-radiant-black/50`}>
          <Icon className={`w-5 h-5 ${pulse ? 'live-dot' : ''}`} />
        </div>
        <span className="text-sm text-radiant-gray">{label}</span>
      </div>
      <p className="text-3xl font-mono font-bold">{value}</p>
    </div>
  );
}

function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}
