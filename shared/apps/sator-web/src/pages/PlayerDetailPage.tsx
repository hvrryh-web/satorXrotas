import { useParams } from 'react-router-dom';
import { usePlayer, useSimRating, useRAR } from '../hooks/useApi';
import { PlayerDetail } from '../components/Players/PlayerDetail';
import { AlertTriangle, Loader2 } from 'lucide-react';

export function PlayerDetailPage() {
  const { id } = useParams<{ id: string }>();
  
  const {
    data: player,
    isLoading: playerLoading,
    error: playerError,
  } = usePlayer(id || '', {
    enabled: !!id,
  });

  const { data: simRating, isLoading: simRatingLoading } = useSimRating(id || '', undefined, {
    enabled: !!id,
  });

  const { data: rar, isLoading: rarLoading } = useRAR(id || '', {
    enabled: !!id,
  });

  if (playerLoading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="flex items-center gap-3 text-radiant-gray">
          <Loader2 className="w-6 h-6 animate-spin" />
          <span>Loading player data...</span>
        </div>
      </div>
    );
  }

  if (playerError || !player) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-radiant-red/10 rounded-full flex items-center justify-center">
            <AlertTriangle className="w-8 h-8 text-radiant-red" />
          </div>
          <h2 className="text-xl font-bold mb-2">Player Not Found</h2>
          <p className="text-radiant-gray">
            The player you are looking for does not exist or has been removed.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <PlayerDetail
        player={player}
        simRating={simRating}
        rar={rar}
        isLoadingAnalytics={simRatingLoading || rarLoading}
      />
    </div>
  );
}
