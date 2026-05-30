/**
 * Lane E (Task E1.2) — Pricing page.
 *
 * Tier table from docs/product/PRICING.md (intent: 3-tier free → premium
 * → team). When PRD pricing changes, regenerate this page or pull from
 * the canonical source.
 */

import type { Metadata, Route } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Pricing — NJZ RAT-OS',
  description: 'Free for individual habit-building; Premium for advanced module surfaces; Team for shared cohorts.',
};

const PALETTE = {
  bg: '#0F172A',
  bgElevated: '#1E293B',
  text: '#F8FAFC',
  textMuted: '#94A3B8',
  accent: '#14B8A6',
  warm: '#F97316',
};

const TIERS = [
  {
    name: 'Free',
    price: '$0',
    cadence: 'forever',
    accent: '#94A3B8',
    blurb: 'Daily habit-building for individuals.',
    features: [
      'All 7 modules at base level',
      'Focus Hero — Pomodoro / Deep Work / Sprint',
      '5 baseline soundscapes',
      'Distraction Blocker — in-app + extension',
      '7-day session history',
      'Single device sync',
    ],
  },
  {
    name: 'Premium',
    price: '$8',
    cadence: 'per month',
    accent: '#F97316',
    blurb: 'Advanced surfaces + creator exports + cognitive depth.',
    features: [
      'Everything in Free',
      'Custom soundscape builder',
      'Deep Canvas gallery',
      'Manuscript EPUB + DOCX export',
      'Historical Trends 30 / 60 / 90 days',
      'Cognitive Age + percentile bands',
      'Calendar integration (Google + Apple)',
      'Unlimited session history',
      'Multi-device sync',
      'Premium card themes',
    ],
    cta: 'Start free trial',
    highlight: true,
  },
  {
    name: 'Team',
    price: '$24',
    cadence: 'per seat / month',
    accent: '#14B8A6',
    blurb: 'Shared cohorts + aggregate dashboards.',
    features: [
      'Everything in Premium',
      'Shared cohort dashboards',
      'Team-wide focus streaks',
      'SSO (Google Workspace, Okta)',
      'Aggregate analytics export',
      'Priority support',
    ],
  },
];

export default function PricingPage() {
  return (
    <main
      style={{
        minHeight: '100vh',
        background: PALETTE.bg,
        color: PALETTE.text,
        fontFamily: 'system-ui, -apple-system, sans-serif',
        padding: '4rem 1.5rem',
        maxWidth: 1100,
        margin: '0 auto',
      }}
    >
      <header style={{ textAlign: 'center' }}>
        <h1 style={{ fontSize: '3rem', margin: 0, letterSpacing: '-0.03em' }}>Pricing</h1>
        <p style={{ marginTop: '1rem', color: PALETTE.textMuted, fontSize: '1.125rem' }}>
          Free for individual habit-building. Premium for the full surface.
          Team for shared cohorts.
        </p>
      </header>

      <section
        style={{
          marginTop: '3rem',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '1.5rem',
        }}
      >
        {TIERS.map((t) => (
          <article
            key={t.name}
            style={{
              background: PALETTE.bgElevated,
              padding: '1.75rem',
              borderRadius: 2,
              borderTop: `4px solid ${t.accent}`,
              outline: t.highlight ? `1px solid ${t.accent}` : undefined,
              outlineOffset: t.highlight ? 4 : undefined,
            }}
          >
            <h2 style={{ margin: 0, fontSize: '1.25rem' }}>{t.name}</h2>
            <p style={{ margin: '0.5rem 0 0', color: PALETTE.textMuted, fontSize: '0.95rem' }}>{t.blurb}</p>
            <div style={{ marginTop: '1.25rem' }}>
              <span style={{ fontSize: '2rem', fontWeight: 700 }}>{t.price}</span>
              <span style={{ color: PALETTE.textMuted, marginLeft: '0.4rem' }}>{t.cadence}</span>
            </div>
            <ul style={{ marginTop: '1.25rem', paddingLeft: '1.25rem', color: PALETTE.text, lineHeight: 1.65 }}>
              {t.features.map((f) => (
                <li key={f} style={{ fontSize: '0.95rem' }}>{f}</li>
              ))}
            </ul>
            {t.cta && (
              <Link
                href={'/' as Route}
                style={{
                  display: 'inline-block',
                  marginTop: '1.5rem',
                  padding: '0.6rem 1.25rem',
                  background: t.accent,
                  color: PALETTE.bg,
                  borderRadius: 2,
                  textDecoration: 'none',
                  fontWeight: 500,
                }}
              >
                {t.cta}
              </Link>
            )}
          </article>
        ))}
      </section>

      <p style={{ marginTop: '3rem', color: PALETTE.textMuted, fontSize: '0.875rem', textAlign: 'center' }}>
        Prices in USD. Plans renew monthly until cancelled. EU + UK pricing
        includes applicable VAT.
      </p>
    </main>
  );
}
