import type { UserId } from '@njz-os/core';

export interface IdentityConfig {
  baseUrl: string;
}

export interface AuthSession {
  userId: UserId;
  expiresAt: string;
  tier: 'free' | 'premium' | 'team';
}

export class IdentityError extends Error {
  constructor(
    message: string,
    public readonly code: string,
  ) {
    super(message);
    this.name = 'IdentityError';
  }
}

export interface IdentityClient {
  currentSession(): Promise<AuthSession | null>;
  signOut(): Promise<void>;
}

/** Phase 0 stub. Real implementation in Phase 1 once auth ADR is accepted. */
export function createIdentityClient(_config: IdentityConfig): IdentityClient {
  return {
    async currentSession() {
      return null;
    },
    async signOut() {
      /* no-op */
    },
  };
}
