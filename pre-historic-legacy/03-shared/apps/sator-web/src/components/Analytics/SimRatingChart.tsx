import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import type { SimRatingBreakdown } from '../../types';

interface SimRatingChartProps {
  data: SimRatingBreakdown;
}

export function SimRatingChart({ data }: SimRatingChartProps) {
  const chartData = [
    {
      stat: 'Kills',
      value: normalizeZScore(data.z_scores.kills),
      fullMark: 100,
    },
    {
      stat: 'Deaths',
      value: normalizeZScore(data.z_scores.deaths) * -1, // Invert since lower deaths is better
      fullMark: 100,
    },
    {
      stat: 'Kill Value',
      value: normalizeZScore(data.z_scores.adjusted_kill_value),
      fullMark: 100,
    },
    {
      stat: 'ADR',
      value: normalizeZScore(data.z_scores.adr),
      fullMark: 100,
    },
    {
      stat: 'KAST',
      value: normalizeZScore(data.z_scores.kast_pct),
      fullMark: 100,
    },
  ];

  const overallRating = data.sim_rating;

  return (
    <div className="space-y-4">
      {/* Overall Rating */}
      <div className="flex items-center justify-center p-4 bg-radiant-black rounded-lg">
        <div className="text-center">
          <p className="text-sm text-radiant-gray mb-1">Overall SimRating</p>
          <p
            className={`text-4xl font-mono font-bold ${
              overallRating >= 1.2
                ? 'text-radiant-gold'
                : overallRating >= 1.0
                ? 'text-radiant-cyan'
                : 'text-radiant-gray'
            }`}
          >
            {overallRating.toFixed(2)}
          </p>
        </div>
      </div>

      {/* Radar Chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <PolarGrid stroke="#2a2a3a" />
            <PolarAngleAxis
              dataKey="stat"
              tick={{ fill: '#8a8a9a', fontSize: 12 }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={false}
              axisLine={false}
            />
            <Radar
              name="Player Stats"
              dataKey="value"
              stroke="#ff4655"
              strokeWidth={2}
              fill="#ff4655"
              fillOpacity={0.3}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-radiant-card border border-radiant-border rounded-lg p-3 shadow-lg">
                      <p className="text-sm font-medium">{payload[0].payload.stat}</p>
                      <p className="text-lg font-mono font-bold text-radiant-red">
                        {payload[0].value?.toFixed(1)}
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Component Breakdown */}
      <div className="grid grid-cols-2 gap-3">
        <ComponentItem label="Kills" value={data.components.kills} />
        <ComponentItem label="Deaths" value={data.components.deaths} />
        <ComponentItem label="Kill Value" value={data.components.adjusted_kill_value} />
        <ComponentItem label="ADR" value={data.components.adr} />
        <ComponentItem label="KAST" value={data.components.kast} />
      </div>
    </div>
  );
}

function ComponentItem({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between p-2 bg-radiant-black rounded">
      <span className="text-sm text-radiant-gray">{label}</span>
      <span className="text-sm font-mono font-medium">{value.toFixed(2)}</span>
    </div>
  );
}

// Normalize z-score to 0-100 scale for visualization
function normalizeZScore(zScore: number): number {
  // Typical z-scores range from -3 to +3
  // Map to 0-100 with 50 being average
  const normalized = ((zScore + 3) / 6) * 100;
  return Math.max(0, Math.min(100, normalized));
}
