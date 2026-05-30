/**
 * Lane E — Identity types.
 *
 * The identity surface is intentionally provider-agnostic so the same
 * webapp code paths work with Supabase (production), a mock (dev), or
 * any future provider. Per ADR-0013, Supabase Auth is the Phase-1
 * primary; the mock is the test + Phase-0-migration story.
 */

import { z } from 'zod';

export const tierSchema = z.enum(['free', 'premium', 'team']);
export type Tier = z.infer<typeof tierSchema>;

export const identityUserSchema = z.object({
  id: z.string().min(1),
  email: z.string().email(),
  displayName: z.string().nullable().optional(),
  emailVerified: z.boolean(),
  tier: tierSchema,
  createdAt: z.string().datetime(),
});
export type IdentityUser = z.infer<typeof identityUserSchema>;

export const authSessionSchema = z.object({
  user: identityUserSchema,
  expiresAt: z.string().datetime(),
  /** Refresh-window hint — when ≤ this many ms remain, the consumer should refresh. */
  refreshHintMs: z.number().int().min(0).default(60_000),
});
export type AuthSession = z.infer<typeof authSessionSchema>;

export class IdentityError extends Error {
  constructor(
    message: string,
    public readonly code:
      | 'UNAUTHORIZED'
      | 'NOT_FOUND'
      | 'CONFLICT'
      | 'NETWORK'
      | 'CHALLENGE_REJECTED'
      | 'PROVIDER_ERROR'
      | 'NOT_IMPLEMENTED'
  ) {
    super(message);
    this.name = 'IdentityError';
  }
}

export interface MagicLinkRequestOptions {
  email: string;
  redirectTo?: string;
}

export interface PasskeyEnrollmentChallenge {
  challenge: string;
  rpId: string;
  userIdB64: string;
  userName: string;
  userDisplayName: string;
}

export interface PasskeyAssertionChallenge {
  challenge: string;
  rpId: string;
  allowCredentials?: Array<{ idB64: string }>;
}
