import { Sword, Shield, Crosshair, Zap, Target, Skull } from 'lucide-react';
import type { ExtendedPlayer } from '../../types';

interface StatsTableProps {
  player: ExtendedPlayer;
}

interface StatItem {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
}

export function StatsTable({ player }: StatsTableProps) {
  const stats: StatItem[] = [
    {
      label: 'Kills',
      value: player.kills ?? '-',
      icon: Sword,
      description: 'Total eliminations',
    },
    {
      label: 'Deaths',
      value: player.deaths ?? '-',
      icon: Skull,
      description: 'Total deaths',
    },
    {
      label: 'K/D Ratio',
      value: calculateKD(player.kills, player.deaths),
      icon: Crosshair,
      description: 'Kills per death',
    },
    {
      label: 'ACS',
      value: player.acs?.toFixed(1) ?? '-',
      icon: Zap,
      description: 'Average Combat Score',
    },
    {
      label: 'ADR',
      value: player.adr?.toFixed(1) ?? '-',
      icon: Target,
      description: 'Average Damage per Round',
    },
    {
      label: 'KAST%',
      value: player.kast_pct ? `${player.kast_pct.toFixed(1)}%` : '-',
      icon: Shield,
      description: 'Kill, Assist, Survive, Trade %',
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <div
            key={stat.label}
            className="flex items-center gap-4 p-4 bg-radiant-black rounded-lg"
          >
            <div className="p-3 bg-radiant-card rounded-lg">
              <Icon className="w-5 h-5 text-radiant-cyan" />
            </div>
            <div>
              <p className="text-sm text-radiant-gray">{stat.label}</p>
              <p className="text-xl font-mono font-semibold">{stat.value}</p>
              {stat.description && (
                <p className="text-xs text-radiant-gray/60">{stat.description}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function calculateKD(kills?: number, deaths?: number): string {
  if (!kills || !deaths || deaths === 0) return '-';
  return (kills / deaths).toFixed(2);
}
