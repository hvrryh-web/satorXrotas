/**
 * Lane E — In-memory mock IdentityProvider.
 *
 * Used in tests and during development before Supabase credentials are
 * wired. Implements the full IdentityProvider surface with deterministic
 * behaviour so suites can pin user/session state.
 */

import type { IdentityProvider } from './provider';
import {
  IdentityError,
  type AuthSession,
  type IdentityUser,
  type MagicLinkRequestOptions,
  type Tier,
} from './types';

export interface MockProviderConfig {
  /** Seed the provider with an already-authenticated user. */
  initialUser?: Partial<IdentityUser> & { email: string };
  /** Default tier for newly-created users (test path). */
  defaultTier?: Tier;
  /** Maximum sessions to keep in history (default 10). */
  historyCap?: number;
}

export function createMockIdentityProvider(
  config: MockProviderConfig = {}
): IdentityProvider & {
  /** Test helpers — not part of the public IdentityProvider interface. */
  __test__: {
    setSession(user: Partial<IdentityUser> & { email: string }): void;
    listEnrolledPasskeys(): string[];
    flushPendingMagicLinks(): MagicLinkRequestOptions[];
  };
} {
  let session: AuthSession | null = null;
  const enrolledPasskeys: string[] = [];
  const pendingMagicLinks: MagicLinkRequestOptions[] = [];

  const buildUser = (
    partial: Partial<IdentityUser> & { email: string }
  ): IdentityUser => ({
    id: partial.id ?? `u_${Math.random().toString(36).slice(2, 10)}`,
    email: partial.email,
    displayName: partial.displayName ?? null,
    emailVerified: partial.emailVerified ?? true,
    tier: partial.tier ?? config.defaultTier ?? 'free',
    createdAt: partial.createdAt ?? new Date().toISOString(),
  });

  const setSession = (
    partial: Partial<IdentityUser> & { email: string }
  ): void => {
    const user = buildUser(partial);
    session = {
      user,
      expiresAt: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
      refreshHintMs: 60_000,
    };
  };

  if (config.initialUser) setSession(config.initialUser);

  return {
    async currentSession() {
      return session;
    },

    async requestMagicLink(opts) {
      pendingMagicLinks.push(opts);
      return { trackingId: `magic_${Math.random().toString(36).slice(2)}` };
    },

    async beginPasskeyEnrollment() {
      if (!session) throw new IdentityError('Sign in first', 'UNAUTHORIZED');
      const idBase64 =
        typeof globalThis.btoa === 'function'
          ? globalThis.btoa(session.user.id)
          : session.user.id;
      return {
        challenge: Math.random().toString(36).slice(2),
        rpId: 'mock.njz-os.app',
        userIdB64: idBase64,
        userName: session.user.email,
        userDisplayName: session.user.displayName ?? session.user.email,
      };
    },

    async completePasskeyEnrollment(credential) {
      if (!session) throw new IdentityError('Sign in first', 'UNAUTHORIZED');
      enrolledPasskeys.push(credential.idB64);
    },

    async beginPasskeyAssertion() {
      return {
        challenge: Math.random().toString(36).slice(2),
        rpId: 'mock.njz-os.app',
        allowCredentials: enrolledPasskeys.map((idB64) => ({ idB64 })),
      };
    },

    async completePasskeyAssertion(assertion) {
      if (!enrolledPasskeys.includes(assertion.idB64)) {
        throw new IdentityError(
          'Unknown credential',
          'CHALLENGE_REJECTED'
        );
      }
      if (!session) {
        setSession({ email: 'test@example.com' });
      }
      return session!;
    },

    async signOut() {
      session = null;
    },

    async deleteAccount() {
      if (!session) throw new IdentityError('No session to delete', 'UNAUTHORIZED');
      session = null;
      enrolledPasskeys.length = 0;
    },

    __test__: {
      setSession,
      listEnrolledPasskeys() {
        return enrolledPasskeys.slice();
      },
      flushPendingMagicLinks() {
        const out = pendingMagicLinks.slice();
        pendingMagicLinks.length = 0;
        return out;
      },
    },
  };
}
