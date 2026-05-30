/**
 * Lane E — Identity surface.
 *
 * Public entrypoint. `createIdentityClient` returns the high-level client
 * used by apps/web; the concrete provider is injected.
 *
 *   const provider = createMockIdentityProvider({ initialUser: { email: 'dev@x' } });
 *   const client = createIdentityClient({ provider });
 *   await client.currentSession();
 *
 * Legacy Phase-0 stub retained as `createLegacyIdentityClient` +
 * `LegacyAuthSession` for backward compatibility while existing imports
 * migrate.
 */

import type { UserId } from '@njz-os/core';
import type { IdentityProvider } from './provider';
import { IdentityError, type AuthSession } from './types';

export * from './types';
export * from './provider';
export * from './mock';

export interface IdentityClientConfig {
  provider: IdentityProvider;
}

export interface IdentityClient {
  readonly provider: IdentityProvider;
  currentSession(): Promise<AuthSession | null>;
  signOut(): Promise<void>;
  deleteAccount(): Promise<void>;
}

export function createIdentityClient(config: IdentityClientConfig): IdentityClient {
  return {
    provider: config.provider,
    currentSession() {
      return config.provider.currentSession();
    },
    signOut() {
      return config.provider.signOut();
    },
    deleteAccount() {
      return config.provider.deleteAccount();
    },
  };
}

/** @deprecated Phase-0 stub. Migrate to `createIdentityClient` + provider. */
export interface LegacyAuthSession {
  userId: UserId;
  expiresAt: string;
  tier: 'free' | 'premium' | 'team';
}

/** @deprecated Phase-0 stub. Migrate to `createIdentityClient` + provider. */
export interface LegacyIdentityClient {
  currentSession(): Promise<LegacyAuthSession | null>;
  signOut(): Promise<void>;
}

export function createLegacyIdentityClient(): LegacyIdentityClient {
  return {
    async currentSession() {
      return null;
    },
    async signOut() {
      throw new IdentityError(
        'legacy identity-client stub — migrate to createIdentityClient',
        'NOT_IMPLEMENTED'
      );
    },
  };
}
