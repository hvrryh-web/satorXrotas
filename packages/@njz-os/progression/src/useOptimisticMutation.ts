/**
 * PRX-25-ENH-02 — Optimistic UI mutation helper.
 *
 * Thin wrapper over TanStack Query's `useMutation` that:
 *   - applies an optimistic update to the relevant cache keys
 *     immediately on `mutate()`,
 *   - rolls back on error,
 *   - lets the caller fire a toast on success/error via the @njz-os/ui
 *     hook (caller wires that — no UI dep here).
 *
 * Typical use (W — manuscript autosave):
 *
 *   const m = useOptimisticMutation({
 *     mutationFn: (body) => client.upsertManuscript(body),
 *     queryKey: manuscriptQueryKey(userId, manuscriptId),
 *     applyOptimistic: (prev, body) => ({ ...prev, ...body }),
 *   });
 *
 *   m.mutate({ title: 'Chapter 1', body: '…' });
 */

import {
  useMutation,
  useQueryClient,
  type UseMutationOptions,
  type UseMutationResult,
} from '@tanstack/react-query';

export interface OptimisticMutationOptions<TData, TVariables, TPrev>
  extends Omit<UseMutationOptions<TData, Error, TVariables, { previous: TPrev | undefined }>, 'onMutate' | 'onError' | 'onSettled'> {
  queryKey: readonly unknown[];
  applyOptimistic: (previous: TPrev | undefined, variables: TVariables) => TPrev;
  onSuccessToast?: (data: TData, variables: TVariables) => void;
  onErrorToast?: (err: Error, variables: TVariables) => void;
}

export function useOptimisticMutation<TData, TVariables, TPrev>(
  opts: OptimisticMutationOptions<TData, TVariables, TPrev>
): UseMutationResult<TData, Error, TVariables, { previous: TPrev | undefined }> {
  const queryClient = useQueryClient();
  const { queryKey, applyOptimistic, onSuccessToast, onErrorToast, ...rest } = opts;

  return useMutation({
    ...rest,
    onMutate: async (variables) => {
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData<TPrev>(queryKey);
      queryClient.setQueryData<TPrev>(queryKey, (curr) =>
        applyOptimistic(curr as TPrev | undefined, variables)
      );
      return { previous };
    },
    onError: (err, variables, context) => {
      if (context && context.previous !== undefined) {
        queryClient.setQueryData(queryKey, context.previous);
      }
      onErrorToast?.(err, variables);
    },
    onSuccess: (data, variables) => {
      onSuccessToast?.(data, variables);
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });
}
