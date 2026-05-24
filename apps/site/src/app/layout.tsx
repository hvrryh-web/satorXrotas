import type { ReactNode } from 'react';

export const metadata = {
  title: 'NJZ RAT-OS — Your Neural Operating System',
  description:
    'Train. Focus. Create. Learn. Grow. A unified wellness-productivity OS that replaces your fragmented app stack with one cohesive cognitive environment.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
