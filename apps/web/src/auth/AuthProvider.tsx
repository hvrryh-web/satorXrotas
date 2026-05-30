/**
 * Lane E — AuthProvider (Task E5).
 *
 * Owns the identity client + current session state for the webapp.
 * Children consume via `useAuth()` for the session + `useTier()` for
 * the gating helper.
 *
 * Phase 1 wires this to a mock provider; flipping to Supabase is one
 * line at construction (`provider: createSupabaseProvider(env)`).
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import {
  createIdentityClient,
  createMockIdentityProvider,
  type AuthSession,
  type IdentityClient,
  type IdentityProvider,
  type Tier,
} from '@njz-os/adapters-identity-client';

export interface AuthContextValue {
  client: IdentityClient;
  session: AuthSession | null;
  isLoading: boolean;
  refresh(): Promise<void>;
  signOut(): Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export interface AuthProviderProps {
  children: ReactNode;
  provider?: IdentityProvider;
}

function defaultProvider(): IdentityProvider {
  if (typeof window !== 'undefined') {
    const stored = window.localStorage.getItem('njz:dev-auth-email');
    if (stored) {
      return createMockIdentityProvider({ initialUser: { email: stored } });
    }
  }
  return createMockIdentityProvider();
}

export function AuthProvider({ children, provider }: AuthProviderProps) {
  const identityProvider = useMemo(() => provider ?? defaultProvider(), [provider]);
  const client = useMemo(
    () => createIdentityClient({ provider: identityProvider }),
    [identityProvider]
  );
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      const next = await client.currentSession();
      setSession(next);
    } finally {
      setIsLoading(false);
    }
  }, [client]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const signOut = useCallback(async () => {
    await client.signOut();
    setSession(null);
  }, [client]);

  const value = useMemo<AuthContextValue>(
    () => ({ client, session, isLoading, refresh, signOut }),
    [client, session, isLoading, refresh, signOut]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth() must be called inside <AuthProvider>');
  }
  return ctx;
}

export function useTier(): Tier | null {
  const { session } = useAuth();
  return session?.user.tier ?? null;
}

export function useRequireTier(minimum: Tier): { allowed: boolean; current: Tier | null } {
  const tier = useTier();
  const allowed = matchTier(tier, minimum);
  return { allowed, current: tier };
}

const TIER_ORDER: Record<Tier, number> = { free: 0, premium: 1, team: 2 };

function matchTier(current: Tier | null, minimum: Tier): boolean {
  if (!current) return false;
  return TIER_ORDER[current] >= TIER_ORDER[minimum];
}
