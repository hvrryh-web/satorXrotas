import { describe, expect, it } from 'vitest';
import { createMockIdentityProvider } from './mock';
import { IdentityError } from './types';
import { createIdentityClient, requireSession } from './index';

describe('mock identity provider', () => {
  it('starts unauthenticated when no initialUser given', async () => {
    const provider = createMockIdentityProvider();
    expect(await provider.currentSession()).toBeNull();
  });

  it('initialUser produces a valid session', async () => {
    const provider = createMockIdentityProvider({ initialUser: { email: 'a@b.com' } });
    const session = await provider.currentSession();
    expect(session?.user.email).toBe('a@b.com');
    expect(session?.user.tier).toBe('free');
    expect(session?.expiresAt).toBeDefined();
  });

  it('passkey enrollment requires a session, then registers the credential', async () => {
    const provider = createMockIdentityProvider();
    await expect(provider.beginPasskeyEnrollment()).rejects.toBeInstanceOf(IdentityError);
    provider.__test__.setSession({ email: 'a@b.com' });
    const challenge = await provider.beginPasskeyEnrollment();
    expect(challenge.userName).toBe('a@b.com');
    await provider.completePasskeyEnrollment({
      idB64: 'cred-1',
      publicKeyB64: 'pk',
      clientDataJsonB64: 'cd',
      attestationObjectB64: 'ao',
    });
    expect(provider.__test__.listEnrolledPasskeys()).toEqual(['cred-1']);
  });

  it('passkey assertion fails for unknown credentials', async () => {
    const provider = createMockIdentityProvider();
    await provider.beginPasskeyAssertion();
    await expect(
      provider.completePasskeyAssertion({
        idB64: 'unknown',
        authenticatorDataB64: 'a',
        clientDataJsonB64: 'b',
        signatureB64: 'c',
      })
    ).rejects.toBeInstanceOf(IdentityError);
  });

  it('signOut clears the session', async () => {
    const provider = createMockIdentityProvider({ initialUser: { email: 'a@b.com' } });
    expect(await provider.currentSession()).not.toBeNull();
    await provider.signOut();
    expect(await provider.currentSession()).toBeNull();
  });

  it('deleteAccount clears session + enrolled passkeys', async () => {
    const provider = createMockIdentityProvider({ initialUser: { email: 'a@b.com' } });
    await provider.completePasskeyEnrollment({
      idB64: 'cred-1',
      publicKeyB64: 'pk',
      clientDataJsonB64: 'cd',
      attestationObjectB64: 'ao',
    });
    await provider.deleteAccount();
    expect(await provider.currentSession()).toBeNull();
    expect(provider.__test__.listEnrolledPasskeys()).toEqual([]);
  });

  it('requestMagicLink records the request and returns a tracking id', async () => {
    const provider = createMockIdentityProvider();
    const res = await provider.requestMagicLink({ email: 'a@b.com' });
    expect(res.trackingId).toMatch(/^magic_/);
    const pending = provider.__test__.flushPendingMagicLinks();
    expect(pending).toEqual([{ email: 'a@b.com' }]);
  });
});

describe('createIdentityClient', () => {
  it('passes through to provider methods', async () => {
    const provider = createMockIdentityProvider({ initialUser: { email: 'a@b.com' } });
    const client = createIdentityClient({ provider });
    expect(await client.currentSession()).not.toBeNull();
    await client.signOut();
    expect(await client.currentSession()).toBeNull();
  });
});

describe('requireSession', () => {
  it('returns session when authenticated', async () => {
    const provider = createMockIdentityProvider({ initialUser: { email: 'a@b.com' } });
    const session = await requireSession(provider);
    expect(session.user.email).toBe('a@b.com');
  });

  it('throws when unauthenticated', async () => {
    const provider = createMockIdentityProvider();
    await expect(requireSession(provider)).rejects.toBeInstanceOf(IdentityError);
  });
});
