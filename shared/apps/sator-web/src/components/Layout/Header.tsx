import { Link, useLocation } from 'react-router-dom';
import { Search, Menu, X, Zap } from 'lucide-react';
import { useState } from 'react';

const navItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/matches', label: 'Matches' },
  { path: '/players', label: 'Players' },
  { path: '/analytics', label: 'Analytics' },
];

export function Header() {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-radiant-black/90 backdrop-blur-md border-b border-radiant-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-8 h-8 bg-gradient-to-br from-radiant-red to-radiant-orange rounded-lg flex items-center justify-center transition-transform group-hover:scale-105">
              <span className="font-bold text-sm">S</span>
            </div>
            <span className="font-bold text-xl tracking-tight">
              SATOR
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
                  isActive(item.path)
                    ? 'text-white bg-radiant-card'
                    : 'text-radiant-gray hover:text-white hover:bg-radiant-card/50'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          {/* Right Side Actions */}
          <div className="flex items-center gap-4">
            {/* Search Button */}
            <button
              className="hidden sm:flex items-center gap-2 px-3 py-1.5 text-sm text-radiant-gray hover:text-white bg-radiant-card hover:bg-radiant-border rounded-lg border border-radiant-border transition-all"
              onClick={() => {
                // Could open a search modal
                document.getElementById('global-search')?.focus();
              }}
            >
              <Search className="w-4 h-4" />
              <span className="hidden lg:inline">Search...</span>
              <kbd className="hidden lg:inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-mono bg-radiant-border rounded">
                ⌘K
              </kbd>
            </button>

            {/* Live Indicator */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-radiant-red/10 border border-radiant-red/30 rounded-full">
              <div className="w-2 h-2 bg-radiant-red rounded-full live-dot" />
              <span className="text-xs font-medium text-radiant-red">LIVE</span>
            </div>

            {/* Mobile Menu Button */}
            <button
              className="md:hidden p-2 text-radiant-gray hover:text-white transition-colors"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <nav className="md:hidden py-4 border-t border-radiant-border">
            <div className="flex flex-col gap-2">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-4 py-3 text-sm font-medium rounded-lg transition-all ${
                    isActive(item.path)
                      ? 'text-white bg-radiant-card'
                      : 'text-radiant-gray hover:text-white hover:bg-radiant-card/50'
                  }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </nav>
        )}
      </div>
    </header>
  );
}
