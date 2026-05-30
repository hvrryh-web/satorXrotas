/**
 * Lane E (Task E7) — Account settings + Right-to-Delete.
 */

import { useAuth } from './AuthProvider';
import { useToast } from '@njz-os/ui';
import { useNavigate } from 'react-router-dom';

export function AccountRoute() {
  const { session, client, signOut } = useAuth();
  const { notify } = useToast();
  const navigate = useNavigate();

  if (!session) {
    return (
      <div className="rat-page">
        <h1>Account</h1>
        <p>You&rsquo;re not signed in.</p>
      </div>
    );
  }

  const onSignOut = async () => {
    await signOut();
    window.localStorage.removeItem('njz:dev-auth-email');
    notify('Signed out', { variant: 'info' });
    navigate('/');
  };

  const onDelete = async () => {
    const ok = window.confirm(
      'Delete your account? This cannot be undone. All sessions, streaks, manuscripts, and reviews will be removed.'
    );
    if (!ok) return;
    try {
      await client.deleteAccount();
      window.localStorage.removeItem('njz:dev-auth-email');
      notify('Account deleted', { variant: 'success' });
      navigate('/');
    } catch (err) {
      notify(`Delete failed: ${(err as Error).message}`, { variant: 'error' });
    }
  };

  return (
    <div className="rat-page" style={{ maxWidth: 540 }}>
      <h1>Account</h1>
      <p>
        Signed in as <strong>{session.user.email}</strong> ({session.user.tier}).
      </p>
      <p>Session expires at {new Date(session.expiresAt).toLocaleString()}.</p>

      <h2 style={{ marginTop: 'var(--space-6)' }}>Sign out</h2>
      <button
        type="button"
        onClick={onSignOut}
        style={{
          padding: 'var(--space-2) var(--space-4)',
          borderRadius: 'var(--radius-sharp)',
          border: '1px solid var(--bg-elevated)',
          background: 'transparent',
          color: 'var(--text)',
          cursor: 'pointer',
        }}
      >
        Sign out
      </button>

      <h2 style={{ marginTop: 'var(--space-6)' }}>Delete account</h2>
      <p>This removes your account, sessions, and all module data. Irrevocable.</p>
      <button
        type="button"
        onClick={onDelete}
        style={{
          padding: 'var(--space-2) var(--space-4)',
          borderRadius: 'var(--radius-sharp)',
          border: '1px solid var(--danger)',
          background: 'transparent',
          color: 'var(--danger)',
          cursor: 'pointer',
        }}
      >
        Delete account
      </button>
    </div>
  );
}
