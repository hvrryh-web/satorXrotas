import { Suspense } from 'react';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Brain Training — NJZ RAT-OS',
  description:
    'Five science-grounded games + adaptive difficulty + your Cognitive Profile + a guided My Journey progression arc.',
  openGraph: {
    title: 'Brain Training — NJZ RAT-OS',
    description:
      'Five science-grounded games + adaptive difficulty + your Cognitive Profile + a guided My Journey progression arc.',
    type: 'website',
  },
};

const PALETTE = {
  bg: '#0F172A',
  bgElevated: '#1E293B',
  text: '#F8FAFC',
  textMuted: '#94A3B8',
  accent: '#22C55E',
};

function JsonLd() {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'Brain Training — NJZ RAT-OS',
    operatingSystem: 'Web',
    applicationCategory: 'HealthApplication',
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
  await new Promise((resolve) => setTimeout(resolve, 0));
  const features = [
    { title: 'Five games', body: 'Recall Wheel, Pattern Flow, Logic Bridge, Spatial Drift, Numeric Pulse.' },
    { title: 'Adaptive bounds', body: '±15 % per session, ±30 % per day — no demoralising spikes.' },
    { title: 'Cognitive Profile', body: 'Five-axis vector + cohort percentile band, updated weekly.' },
    { title: 'My Journey', body: '12-week guided arc that ties games to milestones outside training.' },
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

export default function BrainTrainingPage() {
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
          Brain Training
        </h1>
        <p style={{ fontSize: '1.25rem', marginTop: '1rem', color: PALETTE.textMuted }}>
          Five science-grounded games + adaptive difficulty + your Cognitive
          Profile + a guided My Journey progression arc — designed to make
          cognitive maintenance feel like fun, not homework.
        </p>
      </header>

      <Suspense
        fallback={<p style={{ marginTop: '4rem', color: PALETTE.textMuted }}>Loading features…</p>}
      >
        <FeatureGrid />
      </Suspense>
    </main>
  );
}
