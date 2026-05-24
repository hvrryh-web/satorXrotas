import type { NextConfig } from 'next';

const config: NextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@njz-os/ui', '@njz-os/core'],
  experimental: {
    typedRoutes: true,
  },
};

export default config;
