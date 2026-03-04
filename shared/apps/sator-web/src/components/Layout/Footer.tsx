import { Github, Twitter, MessageCircle, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';

const footerLinks = {
  platform: [
    { label: 'Dashboard', href: '/' },
    { label: 'Players', href: '/players' },
    { label: 'Matches', href: '/matches' },
    { label: 'Analytics', href: '/analytics' },
  ],
  resources: [
    { label: 'API Documentation', href: '/docs/api' },
    { label: 'Data Dictionary', href: '/docs/data' },
    { label: 'SATOR Architecture', href: '/docs/architecture' },
  ],
  community: [
    { label: 'GitHub', href: 'https://github.com', icon: Github },
    { label: 'Twitter', href: 'https://twitter.com', icon: Twitter },
    { label: 'Discord', href: 'https://discord.com', icon: MessageCircle },
  ],
};

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-radiant-border bg-radiant-black lg:ml-64">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <Link to="/" className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 bg-gradient-to-br from-radiant-red to-radiant-orange rounded-lg flex items-center justify-center">
                <span className="font-bold text-sm">S</span>
              </div>
              <span className="font-bold text-xl">SATOR</span>
            </Link>
            <p className="text-sm text-radiant-gray mb-4">
              Advanced esports analytics platform powered by the SATOR engine.
            </p>
            <div className="flex items-center gap-4">
              {footerLinks.community.map((link) => {
                const Icon = link.icon;
                return (
                  <a
                    key={link.label}
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-radiant-gray hover:text-white transition-colors"
                    aria-label={link.label}
                  >
                    <Icon className="w-5 h-5" />
                  </a>
                );
              })}
            </div>
          </div>

          {/* Platform Links */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider mb-4">Platform</h3>
            <ul className="space-y-2">
              {footerLinks.platform.map((link) => (
                <li key={link.label}>
                  <Link
                    to={link.href}
                    className="text-sm text-radiant-gray hover:text-white transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider mb-4">Resources</h3>
            <ul className="space-y-2">
              {footerLinks.resources.map((link) => (
                <li key={link.label}>
                  <Link
                    to={link.href}
                    className="text-sm text-radiant-gray hover:text-white transition-colors inline-flex items-center gap-1"
                  >
                    {link.label}
                    {link.href.startsWith('http') && (
                      <ExternalLink className="w-3 h-3" />
                    )}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Newsletter / Updates */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider mb-4">Stay Updated</h3>
            <p className="text-sm text-radiant-gray mb-4">
              Get the latest analytics updates and features.
            </p>
            <form className="flex gap-2" onSubmit={(e) => e.preventDefault()}>
              <input
                type="email"
                placeholder="Email address"
                className="flex-1 px-3 py-2 bg-radiant-card border border-radiant-border rounded-lg text-sm placeholder-radiant-gray focus:outline-none focus:border-radiant-red/50"
              />
              <button
                type="submit"
                className="px-4 py-2 bg-radiant-red hover:bg-radiant-red/90 text-white text-sm font-medium rounded-lg transition-colors"
              >
                Subscribe
              </button>
            </form>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-8 border-t border-radiant-border flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-radiant-gray">
            © {currentYear} SATOR Analytics. All rights reserved.
          </p>
          <div className="flex items-center gap-6 text-sm text-radiant-gray">
            <Link to="/privacy" className="hover:text-white transition-colors">
              Privacy Policy
            </Link>
            <Link to="/terms" className="hover:text-white transition-colors">
              Terms of Service
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
