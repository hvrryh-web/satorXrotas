import { ArrowUpDown, ArrowUp, ArrowDown, ChevronLeft, ChevronRight } from 'lucide-react';
import type { ExtendedPlayer, PlayerSortField, SortDirection } from '../../types';
import { PlayerCard } from './PlayerCard';

interface PlayerListProps {
  players: ExtendedPlayer[];
  isLoading: boolean;
  sortField: PlayerSortField;
  sortDirection: SortDirection;
  onSort: (field: PlayerSortField) => void;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

const sortableColumns: { key: PlayerSortField; label: string; align: 'left' | 'right' }[] = [
  { key: 'name', label: 'Player', align: 'left' },
  { key: 'acs', label: 'ACS', align: 'right' },
  { key: 'adr', label: 'ADR', align: 'right' },
  { key: 'kast_pct', label: 'KAST%', align: 'right' },
  { key: 'sim_rating', label: 'SimRating', align: 'right' },
  { key: 'rar_score', label: 'RAR', align: 'right' },
];

function SortIcon({
  field,
  currentField,
  direction,
}: {
  field: PlayerSortField;
  currentField: PlayerSortField;
  direction: SortDirection;
}) {
  if (field !== currentField) {
    return <ArrowUpDown className="w-3 h-3 text-radiant-gray opacity-50" />;
  }
  return direction === 'asc' ? (
    <ArrowUp className="w-3 h-3 text-radiant-red" />
  ) : (
    <ArrowDown className="w-3 h-3 text-radiant-red" />
  );
}

export function PlayerList({
  players,
  isLoading,
  sortField,
  sortDirection,
  onSort,
  page,
  totalPages,
  onPageChange,
}: PlayerListProps) {
  if (isLoading) {
    return (
      <div className="bg-radiant-card rounded-xl border border-radiant-border overflow-hidden">
        <div className="p-8 space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 skeleton" />
          ))}
        </div>
      </div>
    );
  }

  if (players.length === 0) {
    return (
      <div className="bg-radiant-card rounded-xl border border-radiant-border p-12 text-center">
        <p className="text-radiant-gray text-lg">No players found</p>
        <p className="text-sm text-radiant-gray/60 mt-2">
          Try adjusting your filters or search query
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Desktop Table View */}
      <div className="hidden md:block bg-radiant-card rounded-xl border border-radiant-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-radiant-border">
                {sortableColumns.map((col) => (
                  <th
                    key={col.key}
                    className={`px-6 py-4 text-xs font-medium text-radiant-gray uppercase tracking-wider cursor-pointer hover:text-white transition-colors ${
                      col.align === 'right' ? 'text-right' : 'text-left'
                    }`}
                    onClick={() => onSort(col.key)}
                  >
                    <div
                      className={`flex items-center gap-2 ${
                        col.align === 'right' ? 'justify-end' : ''
                      }`}
                    >
                      {col.label}
                      <SortIcon field={col.key} currentField={sortField} direction={sortDirection} />
                    </div>
                  </th>
                ))}
                <th className="px-6 py-4 text-xs font-medium text-radiant-gray uppercase tracking-wider text-right">
                  Grade
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-radiant-border/50">
              {players.map((player, index) => (
                <PlayerTableRow key={player.player_id} player={player} index={index} />
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden space-y-4">
        {players.map((player) => (
          <PlayerCard key={player.player_id} player={player} />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-4">
          <p className="text-sm text-radiant-gray">
            Page {page + 1} of {totalPages}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page === 0}
              className="p-2 rounded-lg border border-radiant-border text-radiant-gray hover:text-white hover:bg-radiant-card disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages - 1}
              className="p-2 rounded-lg border border-radiant-border text-radiant-gray hover:text-white hover:bg-radiant-card disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function PlayerTableRow({ player, index }: { player: ExtendedPlayer; index: number }) {
  return (
    <tr className="hover:bg-white/5 transition-colors group">
      <td className="px-6 py-4">
        <div className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm ${
              index < 3
                ? 'bg-gradient-to-br from-radiant-gold to-radiant-orange text-radiant-black'
                : 'bg-radiant-card border border-radiant-border'
            }`}
          >
            {index + 1}
          </div>
          <div>
            <p className="font-medium group-hover:text-radiant-cyan transition-colors">
              {player.name}
            </p>
            <p className="text-xs text-radiant-gray">
              {player.team || 'No Team'} • {player.role || 'Unknown'}
            </p>
          </div>
        </div>
      </td>
      <td className="px-6 py-4 text-right font-mono font-medium">
        {player.acs?.toFixed(1) || '-'}
      </td>
      <td className="px-6 py-4 text-right font-mono">{player.adr?.toFixed(1) || '-'}</td>
      <td className="px-6 py-4 text-right font-mono">
        {player.kast_pct ? `${player.kast_pct.toFixed(1)}%` : '-'}
      </td>
      <td className="px-6 py-4 text-right">
        {player.sim_rating ? (
          <span
            className={`inline-flex items-center px-2 py-1 text-xs font-mono rounded ${
              player.sim_rating >= 1.2
                ? 'bg-radiant-gold/20 text-radiant-gold'
                : player.sim_rating >= 1.0
                ? 'bg-radiant-cyan/20 text-radiant-cyan'
                : 'bg-radiant-gray/20 text-radiant-gray'
            }`}
          >
            {player.sim_rating.toFixed(2)}
          </span>
        ) : (
          '-'
        )}
      </td>
      <td className="px-6 py-4 text-right font-mono">
        {player.rar_score?.toFixed(2) || '-'}
      </td>
      <td className="px-6 py-4 text-right">
        {player.investment_grade ? (
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
        ) : (
          '-'
        )}
      </td>
    </tr>
  );
}
