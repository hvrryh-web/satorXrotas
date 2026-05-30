/**
 * PRX-25-PATCH-02 — Shared progression-state hook.
 *
 * Reads `{ streak, totalXp, level, recentEvents }` from the vaultbrain
 * client via TanStack Query (60s stale window) and subscribes to the
 * default event bus for in-process cache busting on `progression.event`.
 *
 * Used by:
 *   - Lane W manuscript-list header (streak)
 *   - Lane L review session (XP gained on review)
 *   - Lane B′ cognitive-profile header (streak + level)
 *   - Lane A home (heat map; live XP)
 */

import { useEffect } from 'react';
import {
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from '@tanstack/react-query';
import { defaultEventBus } from '@njz-os/core';
import type {
  ProgressionResponse,
  VaultbrainClient,
} from '@njz-os/adapters-vaultbrain-client';

export interface ProgressionView {
  totalXp: number;
  level: number;
  streak: ProgressionResponse['streak'];
  recentEvents: ProgressionResponse['recentEvents'];
}

export interface UseProgressionOptions {
  staleTimeMs?: number;
  enabled?: boolean;
}

export function progressionQueryKey(userId: string): readonly unknown[] {
  return ['progression', userId];
}

export function useProgression(
  client: VaultbrainClient,
  userId: string | null,
  opts?: UseProgressionOptions
): UseQueryResult<ProgressionView, Error> & {
  invalidate: () => Promise<void>;
} {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: progressionQueryKey(userId ?? '__none__'),
    queryFn: async (): Promise<ProgressionView> => {
      if (!userId) throw new Error('useProgression called with null userId');
      const res = await client.getProgression(userId);
      return {
        totalXp: res.totalXp,
        level: res.level,
        streak: res.streak,
        recentEvents: res.recentEvents,
      };
    },
    staleTime: opts?.staleTimeMs ?? 60_000,
    enabled: opts?.enabled !== false && !!userId,
  });

  useEffect(() => {
    if (!userId) return undefined;
    const unsubscribe = defaultEventBus.on('progression.event', (event) => {
      if (event.userId !== (userId as typeof event.userId)) return;
      queryClient.invalidateQueries({ queryKey: progressionQueryKey(userId) });
    });
    return unsubscribe;
  }, [queryClient, userId]);

  const invalidate = (): Promise<void> => {
    if (!userId) return Promise.resolve();
    return queryClient.invalidateQueries({
      queryKey: progressionQueryKey(userId),
    });
  };

  return Object.assign(query, { invalidate });
}
