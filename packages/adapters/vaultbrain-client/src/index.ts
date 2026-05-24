export * from './types';

import type { VaultbrainConfig, VaultbrainEvent } from './types';
import { VaultbrainError } from './types';

export interface VaultbrainClient {
  readonly config: VaultbrainConfig;
  publish<P>(event: VaultbrainEvent<P>): Promise<void>;
  subscribe(handler: (event: VaultbrainEvent) => void): () => void;
  close(): void;
}

/**
 * Phase 0 stub. Phase 1 implementation lands behind G1.vaultbrain-live.
 */
export function createVaultbrainClient(config: VaultbrainConfig): VaultbrainClient {
  const handlers = new Set<(event: VaultbrainEvent) => void>();
  return {
    config,
    async publish() {
      throw new VaultbrainError(
        'vaultbrain-client not implemented in Phase 0',
        'NOT_IMPLEMENTED',
        false,
      );
    },
    subscribe(handler) {
      handlers.add(handler);
      return () => handlers.delete(handler);
    },
    close() {
      handlers.clear();
    },
  };
}
