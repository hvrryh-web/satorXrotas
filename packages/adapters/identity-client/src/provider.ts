/**
 * Lane E — IdentityProvider interface.
 *
 * The webapp consumes this interface; concrete implementations are
 * `createMockProvider` (test + dev) and a future `createSupabaseProvider`
 * (real, lands once Supabase project credentials are wired).
 *
 * The shape is intentionally minimal — high-level surfaces like
 * `createIdentityClient` wrap this and add toast/error-bus emission.
 */

import {
  IdentityError,
  type AuthSession,
  type MagicLinkRequestOptions,
  type PasskeyAssertionChallenge,
  type PasskeyEnrollmentChallenge,
} from './types';

export interface IdentityProvider {
  /** Current session, or null if unauthenticated. Never throws on no-session. */
  currentSession(): Promise<AuthSession | null>;

  /** Request a magic link to the email. Returns a tracking token (provider-specific). */
  requestMagicLink(opts: MagicLinkRequestOptions): Promise<{ trackingId: string }>;

  /** Begin passkey enrollment for a signed-in user. */
  beginPasskeyEnrollment(): Promise<PasskeyEnrollmentChallenge>;

  /** Complete passkey enrollment with the credential the browser returned. */
  completePasskeyEnrollment(credential: {
    idB64: string;
    publicKeyB64: string;
    clientDataJsonB64: string;
    attestationObjectB64: string;
  }): Promise<void>;

  /** Begin passkey sign-in (unauthenticated). */
  beginPasskeyAssertion(): Promise<PasskeyAssertionChallenge>;

  /** Complete passkey sign-in — returns a session on success. */
  completePasskeyAssertion(assertion: {
    idB64: string;
    authenticatorDataB64: string;
    clientDataJsonB64: string;
    signatureB64: string;
    userHandleB64?: string;
  }): Promise<AuthSession>;

  /** Sign out the current session (no-op if no session). */
  signOut(): Promise<void>;

  /** Delete the current user's account permanently. */
  deleteAccount(): Promise<void>;
}

/** Convenience helper: throw rather than return null. */
export async function requireSession(
  provider: IdentityProvider
): Promise<AuthSession> {
  const session = await provider.currentSession();
  if (!session) {
    throw new IdentityError('No active session', 'UNAUTHORIZED');
  }
  return session;
}
