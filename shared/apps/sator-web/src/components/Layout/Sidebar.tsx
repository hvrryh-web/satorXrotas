import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Trophy,
  BarChart3,
  Settings,
  HelpCircle,
  Gamepad2,
  Target,
  TrendingUp,
} from 'lucide-react';

const mainNavItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/players', label: 'Players', icon: Users },
  { path: '/matches', label: 'Matches', icon: Trophy },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
];

const analyticsNavItems = [
  { path: '/analytics/simrating', label: 'SimRating', icon: Target },
  { path: '/analytics/rar', label: 'RAR Scores', icon: TrendingUp },
  { path: '/analytics/investment', label: 'Investment', icon: Gamepad2 },
];

const bottomNavItems = [
  { path: '/settings', label: 'Settings', icon: Settings },
  { path: '/help', label: 'Help', icon: HelpCircle },
];

export function Sidebar() {
  const location = useLocation();
  const isAnalyticsActive = location.pathname.startsWith('/analytics');

  return (
    <aside className="hidden lg:flex flex-col w-64 fixed left-0 top-16 bottom-0 bg-radiant-black border-r border-radiant-border overflow-y-auto">
      {/* Main Navigation */}
      <nav className="flex-1 p-4">
        <div className="space-y-1">
          {mainNavItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-all ${
                    isActive
                      ? 'text-white bg-radiant-red/10 border border-radiant-red/30'
                      : 'text-radiant-gray hover:text-white hover:bg-radiant-card'
                  }`
                }
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </NavLink>
            );
          })}
        </div>

        {/* Analytics Sub-nav */}
        {isAnalyticsActive && (
          <div className="mt-6 pt-6 border-t border-radiant-border">
            <p className="px-4 text-xs font-semibold text-radiant-gray uppercase tracking-wider mb-2">
              Analytics
            </p>
            <div className="space-y-1">
              {analyticsNavItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-4 py-2 text-sm rounded-lg transition-all ${
                        isActive
                          ? 'text-radiant-cyan bg-radiant-cyan/10'
                          : 'text-radiant-gray hover:text-white hover:bg-radiant-card'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4" />
                    {item.label}
                  </NavLink>
                );
              })}
            </div>
          </div>
        )}

        {/* Quick Stats */}
        <div className="mt-6 pt-6 border-t border-radiant-border">
          <p className="px-4 text-xs font-semibold text-radiant-gray uppercase tracking-wider mb-3">
            Platform Stats
          </p>
          <div className="space-y-3 px-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-radiant-gray">Active Matches</span>
              <span className="text-sm font-mono font-medium text-radiant-green">12</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-radiant-gray">Players Tracked</span>
              <span className="text-sm font-mono font-medium text-radiant-cyan">2,847</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-radiant-gray">Data Points</span>
              <span className="text-sm font-mono font-medium text-radiant-gold">12.4M</span>
            </div>
          </div>
        </div>
      </nav>

      {/* Bottom Navigation */}
      <div className="p-4 border-t border-radiant-border">
        <div className="space-y-1">
          {bottomNavItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-2 text-sm font-medium rounded-lg transition-all ${
                    isActive
                      ? 'text-white bg-radiant-card'
                      : 'text-radiant-gray hover:text-white hover:bg-radiant-card/50'
                  }`
                }
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </NavLink>
            );
          })}
        </div>
      </div>
    </aside>
  );
}
