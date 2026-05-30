/**
 * PRX-25-ENH-03 — Streaming SSR demo for /modules/micro-learning.
 *
 * Above-the-fold renders synchronously (target < 200 ms TTFB on Vercel
 * Edge). Below-the-fold streams via React `<Suspense>` boundaries so
 * the largest content can hydrate progressively.
 *
 * Includes JSON-LD `SoftwareApplication` structured data for SEO.
 */

import { Suspense } from 'react';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Micro-Learning — NJZ RAT-OS',
  description:
    'Imprint-style tap-forward cards + SM-2 spaced repetition + a connection-graph that turns every card into a vocabulary unlock.',
  openGraph: {
    title: 'Micro-Learning — NJZ RAT-OS',
    description:
      'Imprint-style tap-forward cards + SM-2 spaced repetition + a connection-graph that turns every card into a vocabulary unlock.',
    type: 'website',
  },
};

const PALETTE = {
  bg: '#0F172A',
  bgElevated: '#1E293B',
  text: '#F8FAFC',
  textMuted: '#94A3B8',
  accent: '#EAB308',
};

function JsonLd() {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'Micro-Learning — NJZ RAT-OS',
    operatingSystem: 'Web',
    applicationCategory: 'EducationalApplication',
    offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
  };
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}

async function FeatureGrid() {
  // Simulated below-the-fold data fetch. In production this would call
  // the CMS or read the prebuilt content index built by Lane L.
  await new Promise((resolve) => setTimeout(resolve, 0));
  const features = [
    { title: 'Imprint-style cards', body: 'Tap-forward reading flow tuned for momentum.' },
    { title: 'SM-2 scheduling', body: 'Canonical spaced-repetition intervals, no leaderboard noise.' },
    { title: 'Connection graph', body: 'Cards earn pills as you learn — vocabulary unlocks naturally.' },
    { title: 'Memory Tomes', body: 'Cross-module unlock with Brain Training Recall Wheel runs.' },
  ];
  return (
    <section style={{ marginTop: '4rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem' }}>
      {features.map((f) => (
        <article
          key={f.title}
          style={{
            background: PALETTE.bgElevated,
            padding: '1.5rem',
            borderRadius: 2,
            borderLeft: `2px solid ${PALETTE.accent}`,
          }}
        >
          <h3 style={{ margin: '0 0 0.5rem', color: PALETTE.text }}>{f.title}</h3>
          <p style={{ margin: 0, color: PALETTE.textMuted, fontSize: '0.95rem' }}>{f.body}</p>
        </article>
      ))}
    </section>
  );
}

export default function MicroLearningPage() {
  return (
    <main
      style={{
        minHeight: '100vh',
        background: PALETTE.bg,
        color: PALETTE.text,
        fontFamily: 'system-ui, -apple-system, sans-serif',
        padding: '4rem 2rem',
        maxWidth: 960,
        margin: '0 auto',
      }}
    >
      <JsonLd />
      <header>
        <h1 style={{ fontSize: '3rem', margin: 0, letterSpacing: '-0.02em' }}>
          Micro-Learning
        </h1>
        <p style={{ fontSize: '1.25rem', marginTop: '1rem', color: PALETTE.textMuted }}>
          Imprint-style tap-forward cards + SM-2 spaced repetition + a
          connection-graph that turns every card into a vocabulary unlock.
        </p>
      </header>

      <Suspense
        fallback={
          <p style={{ marginTop: '4rem', color: PALETTE.textMuted }}>
            Loading features…
          </p>
        }
      >
        <FeatureGrid />
      </Suspense>
    </main>
  );
}
