import { Suspense } from 'react';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Writing Space — NJZ RAT-OS',
  description:
    'Mobile-first chapter editor with focus-session integration and creator-friendly exports.',
  openGraph: {
    title: 'Writing Space — NJZ RAT-OS',
    description:
      'Mobile-first chapter editor with focus-session integration and creator-friendly exports.',
    type: 'website',
  },
};

const PALETTE = {
  bg: '#0F172A',
  bgElevated: '#1E293B',
  text: '#F8FAFC',
  textMuted: '#94A3B8',
  accent: '#0EA5E9',
};

function JsonLd() {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'Writing Space — NJZ RAT-OS',
    operatingSystem: 'Web',
    applicationCategory: 'WritingApplication',
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
    { title: 'Mobile-first editor', body: 'Designed for thumbs — the desktop experience inherits.' },
    { title: 'Chapter scoping', body: 'One chapter per session; word-count budgets keep momentum.' },
    { title: 'Focus integration', body: 'Completing a chapter counts as a Focus Hero session.' },
    { title: 'Creator exports', body: 'PDF free; DOCX + EPUB premium with pandoc fidelity.' },
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

export default function WritingSpacePage() {
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
          Writing Space
        </h1>
        <p style={{ fontSize: '1.25rem', marginTop: '1rem', color: PALETTE.textMuted }}>
          A mobile-first chapter editor for novelists, screenwriters, and
          serial fiction creators — with focus-session integration and
          creator-friendly exports.
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
