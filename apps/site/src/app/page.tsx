/**
 * Lane E (Task E1) — Marketing home.
 *
 * Hero + tagline above the fold (synchronous render); 7-module
 * preview cards below the fold.
 */

import type { Metadata, Route } from 'next';
import Link from 'next/link';
import { Suspense } from 'react';

export const metadata: Metadata = {
  title: 'NJZ RAT-OS — Your Neural Operating System',
  description:
    'A unified wellness-productivity OS combining focus, soundscapes, distraction blocking, writing, micro-learning, brain training, and PolyCo.World — in one cohesive cognitive environment.',
  openGraph: {
    title: 'NJZ RAT-OS',
    description: 'Train. Focus. Create. Learn. Grow.',
    type: 'website',
  },
};

const PALETTE = {
  bg: '#0F172A',
  bgElevated: '#1E293B',
  text: '#F8FAFC',
  textMuted: '#94A3B8',
  accent: '#14B8A6',
  warm: '#F97316',
};

const MODULES = [
  { slug: 'focus-hero', label: 'Focus Hero', tagline: 'XState-driven Pomodoro / Deep Work / Sprint / Flow.', color: '#F97316' },
  { slug: 'soundscapes', label: 'Soundscapes', tagline: 'Web Audio with binaural-beat pairs + Deep Canvas Hush.', color: '#A855F7' },
  { slug: 'distraction-blocker', label: 'Distraction Blocker', tagline: 'Two-tier blocker — in-app SW + Chrome MV3 extension.', color: '#EF4444' },
  { slug: 'writing-space', label: 'Writing Space', tagline: 'Mobile-first chapter editor with creator-friendly exports.', color: '#0EA5E9' },
  { slug: 'micro-learning', label: 'Micro-Learning', tagline: 'Imprint-style cards + SM-2 + connection graph.', color: '#EAB308' },
  { slug: 'brain-training', label: 'Brain Training', tagline: 'Five games + Cognitive Profile + 12-week Journey.', color: '#22C55E' },
  { slug: 'polyco-world', label: 'PolyCo.World', tagline: 'Pixel-art isometric metaverse that grows with progress.', color: '#14B8A6' },
];

async function ModuleGrid() {
  return (
    <section style={{ marginTop: '4rem' }}>
      <h2 style={{ fontSize: '1.5rem', letterSpacing: '-0.01em' }}>Seven modules · one OS</h2>
      <div
        style={{
          marginTop: '1.5rem',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1.25rem',
        }}
      >
        {MODULES.map((m) => (
          <Link
            key={m.slug}
            href={`/modules/${m.slug}` as Route}
            style={{
              background: PALETTE.bgElevated,
              padding: '1.25rem',
              borderRadius: 2,
              borderLeft: `2px solid ${m.color}`,
              color: PALETTE.text,
              textDecoration: 'none',
              display: 'block',
            }}
          >
            <h3 style={{ margin: '0 0 0.4rem', fontSize: '1rem' }}>{m.label}</h3>
            <p style={{ margin: 0, color: PALETTE.textMuted, fontSize: '0.875rem' }}>{m.tagline}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}

export default function HomePage() {
  return (
    <main
      style={{
        minHeight: '100vh',
        background: PALETTE.bg,
        color: PALETTE.text,
        fontFamily: 'system-ui, -apple-system, sans-serif',
        padding: '4rem 1.5rem',
        maxWidth: 1040,
        margin: '0 auto',
      }}
    >
      <header style={{ textAlign: 'center' }}>
        <h1 style={{ fontSize: '3.5rem', margin: 0, letterSpacing: '-0.03em' }}>
          NJZ RAT-OS
        </h1>
        <p style={{ fontSize: '1.5rem', marginTop: '1rem', opacity: 0.85 }}>
          Your Neural Operating System
        </p>
        <p style={{ marginTop: '0.5rem', opacity: 0.65, fontSize: '1.125rem' }}>
          Train. Focus. Create. Learn. Grow.
        </p>
        <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'center', gap: '0.75rem' }}>
          <Link
            href={'/pricing' as Route}
            style={{
              padding: '0.75rem 1.5rem',
              background: PALETTE.accent,
              color: PALETTE.bg,
              borderRadius: 2,
              textDecoration: 'none',
              fontWeight: 500,
            }}
          >
            See pricing
          </Link>
          <Link
            href={'/about' as Route}
            style={{
              padding: '0.75rem 1.5rem',
              border: `1px solid ${PALETTE.bgElevated}`,
              color: PALETTE.text,
              borderRadius: 2,
              textDecoration: 'none',
            }}
          >
            About the thesis
          </Link>
        </div>
      </header>

      <Suspense fallback={<p style={{ marginTop: '4rem', color: PALETTE.textMuted }}>Loading modules…</p>}>
        <ModuleGrid />
      </Suspense>
    </main>
  );
}
