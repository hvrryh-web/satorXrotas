/**
 * Lane E (Task E2.1) — About page.
 *
 * Integration thesis from PRD §1 + ROOT_AXIOMS PR-00.
 */

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'About — NJZ RAT-OS',
  description:
    'One cognitive OS instead of seven separate apps — the integration thesis behind NJZ RAT-OS.',
};

const PALETTE = {
  bg: '#0F172A',
  bgElevated: '#1E293B',
  text: '#F8FAFC',
  textMuted: '#94A3B8',
  accent: '#14B8A6',
};

export default function AboutPage() {
  return (
    <main
      style={{
        minHeight: '100vh',
        background: PALETTE.bg,
        color: PALETTE.text,
        fontFamily: 'system-ui, -apple-system, sans-serif',
        padding: '4rem 1.5rem',
        maxWidth: 760,
        margin: '0 auto',
        lineHeight: 1.65,
      }}
    >
      <header>
        <h1 style={{ fontSize: '3rem', margin: 0, letterSpacing: '-0.03em' }}>About RAT-OS</h1>
        <p style={{ marginTop: '1rem', color: PALETTE.textMuted, fontSize: '1.125rem' }}>
          One cognitive OS instead of seven separate apps.
        </p>
      </header>

      <section style={{ marginTop: '3rem' }}>
        <h2>The thesis</h2>
        <p>
          Modern wellness-productivity tools split your day across seven
          tabs: a focus timer here, an ambient-noise player there, a
          flashcard app you haven&rsquo;t opened in a month, a journal you
          can&rsquo;t find. Each is reasonable in isolation. Together they
          form a fragmented cognitive environment that taxes attention more
          than it relieves it.
        </p>
        <p>
          RAT-OS is built on the wager that integration matters more than
          completeness. Seven modules, one shell, one progression stream.
          A focus session in the morning extends a streak that unlocks a
          decoration in your PolyCo.World office. A chapter completed in
          the writing space counts as a session in the focus engine. A
          card reviewed in micro-learning shows up as XP in your cognitive
          profile.
        </p>
      </section>

      <section style={{ marginTop: '2.5rem' }}>
        <h2>What this isn&rsquo;t</h2>
        <p>
          It isn&rsquo;t a medical device. The binaural beats are produced
          with care; the science on their effects is mixed; we cite the
          honest version of that science. It isn&rsquo;t a productivity
          cult — there&rsquo;s no leaderboard, no shame mechanic, no
          streak you must protect or feel bad about breaking. It
          isn&rsquo;t a walled garden — you own your data, you can export
          everything you&rsquo;ve produced, and you can delete your account
          irrevocably with one click.
        </p>
      </section>

      <section style={{ marginTop: '2.5rem' }}>
        <h2>Building in public</h2>
        <p>
          We&rsquo;re shipping the modules in waves. Phase 1 covers Focus
          Hero, Soundscapes, Distraction Blocker, PolyCo.World office, and
          the auth / onboarding shell. Phase 2 brings Writing Space,
          Micro-Learning, and Brain Training online with their own ADRs
          (editor stack, content licensing, adaptive engine bounds,
          cognitive-profile baseline cohort) settled empirically rather
          than by guess.
        </p>
        <p style={{ marginTop: '1.5rem', color: PALETTE.textMuted, fontSize: '0.95rem' }}>
          Latest progress lives in our&nbsp;
          <a href="https://github.com/hvrryh-web/satorXrotas" style={{ color: PALETTE.accent }}>
            public repo
          </a>
          .
        </p>
      </section>
    </main>
  );
}
