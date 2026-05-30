/**
 * PRX-25-EPIC-01 — Public surface of @njz-os/adapters-vaultbrain-client.
 *
 * The Phase-0 stub (publish/subscribe) remains exported so consumers that
 * had wired against it continue to compile during migration. New code
 * should consume `createVaultbrainClient` for the production-grade
 * HTTP surface.
 */

export * from './types';
export * from './schemas';
export * from './http';
export * from './queue';
export * from './cache';
export * from './client';

import type { VaultbrainConfig, VaultbrainEvent } from './types';
import { VaultbrainError } from './types';

export interface LegacyVaultbrainClient {
  readonly config: VaultbrainConfig;
  publish<P>(event: VaultbrainEvent<P>): Promise<void>;
  subscribe(handler: (event: VaultbrainEvent) => void): () => void;
  close(): void;
}

/**
 * Phase-0 legacy stub. Retained for backwards compatibility while
 * Phase-1 lanes migrate to `createVaultbrainClient` from `./client`.
 *
 * @deprecated Migrate callers to `createVaultbrainClient`.
 */
export function createLegacyVaultbrainClient(
  config: VaultbrainConfig
): LegacyVaultbrainClient {
  const handlers = new Set<(event: VaultbrainEvent) => void>();
  return {
    config,
    async publish() {
      throw new VaultbrainError(
        'legacy vaultbrain-client stub — migrate to createVaultbrainClient',
        'NOT_IMPLEMENTED',
        false
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
