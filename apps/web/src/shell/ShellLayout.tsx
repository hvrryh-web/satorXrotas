import { NavLink, Outlet } from 'react-router-dom';

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
      </header>
      <main className="rat-shell__main">
        <Outlet />
      </main>
    </div>
  );
}
