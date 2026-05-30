/**
 * Lane E (Task E4) — Sign-in route.
 *
 * Phase-1 mock implementation: lets a user "sign in" by entering their
 * email; the mock provider creates an in-memory session. When Supabase
 * is wired, this becomes the magic-link entrypoint + passkey assertion
 * trigger (per ADR-0013).
 */

import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthProvider';
import { useToast } from '@njz-os/ui';

export function SignInRoute() {
  const { client, refresh } = useAuth();
  const { notify } = useToast();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setSubmitting(true);
    try {
      // Phase-1 mock path — persists the email so the provider rehydrates on reload.
      window.localStorage.setItem('njz:dev-auth-email', email);
      await client.provider.requestMagicLink({ email });
      // For the mock, we synthesise an immediate session by re-instantiating
      // through the AuthProvider on next refresh().
      await refresh();
      notify(`Signed in as ${email}`, { variant: 'success' });
      navigate('/');
    } catch (err) {
      notify(`Sign-in failed: ${(err as Error).message}`, { variant: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="rat-page" style={{ maxWidth: 420 }}>
      <h1>Sign in</h1>
      <p>
        Enter your email to receive a magic link. Passkey support arrives
        once Supabase credentials are wired.
      </p>
      <form onSubmit={onSubmit}>
        <label htmlFor="email" style={{ display: 'block', marginBottom: 8 }}>
          Email
        </label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoComplete="email"
          style={{
            width: '100%',
            padding: 'var(--space-3)',
            borderRadius: 'var(--radius-sharp)',
            border: '1px solid var(--bg-elevated)',
            background: 'var(--bg-elevated)',
            color: 'var(--text)',
            fontFamily: 'var(--font-body)',
            fontSize: '1rem',
          }}
        />
        <button
          type="submit"
          disabled={submitting || !email}
          style={{
            marginTop: 'var(--space-4)',
            padding: 'var(--space-3) var(--space-6)',
            borderRadius: 'var(--radius-sharp)',
            border: 'none',
            background: 'var(--accent)',
            color: 'var(--bg)',
            fontFamily: 'var(--font-body)',
            fontSize: '0.875rem',
            cursor: submitting ? 'wait' : 'pointer',
          }}
        >
          {submitting ? 'Signing in…' : 'Send magic link'}
        </button>
      </form>
    </div>
  );
}
