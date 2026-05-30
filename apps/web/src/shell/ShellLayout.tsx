import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';

const modules = [
  { to: '/focus', label: 'Focus' },
  { to: '/sound', label: 'Sound' },
  { to: '/blocker', label: 'Blocker' },
  { to: '/write', label: 'Write' },
  { to: '/learn', label: 'Learn' },
  { to: '/train', label: 'Train' },
  { to: '/world', label: 'World' },
];

export function ShellLayout() {
  const { session, isLoading } = useAuth();
  return (
    <div className="rat-shell">
      <header className="rat-shell__header">
        <NavLink to="/" className="rat-shell__brand">
          NJZ RAT-OS
        </NavLink>
        <nav className="rat-shell__nav">
          {modules.map((m) => (
            <NavLink
              key={m.to}
              to={m.to}
              className={({ isActive }) =>
                `rat-shell__nav-item${isActive ? ' rat-shell__nav-item--active' : ''}`
              }
            >
              {m.label}
            </NavLink>
          ))}
        </nav>
        <div className="rat-shell__auth">
          {isLoading ? (
            <span className="rat-shell__nav-item">…</span>
          ) : session ? (
            <NavLink to="/account" className="rat-shell__nav-item">
              {session.user.email}
            </NavLink>
          ) : (
            <NavLink to="/sign-in" className="rat-shell__nav-item">
              Sign in
            </NavLink>
          )}
        </div>
      </header>
      <main className="rat-shell__main">
        <Outlet />
      </main>
    </div>
  );
}
