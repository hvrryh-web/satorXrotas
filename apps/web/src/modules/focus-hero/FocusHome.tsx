/**
 * Lane A (Task A5) — Focus Hero home view.
 *
 * Mode picker tiles (4 modes) + recent-session list (consumes
 * vaultbrain progression events when wired in a follow-up).
 */

import { MODE_DEFINITIONS, type SessionMode } from '@njz-os/focus-engine';

const MODE_ORDER: SessionMode[] = [
  'pomodoro_25_5',
  'deep_work_50_10',
  'sprint_15_3',
  'flow_90_20',
];

export function FocusHome({
  onStart,
}: {
  onStart: (mode: SessionMode) => void;
}) {
  return (
    <div className="rat-page" style={{ maxWidth: 760 }}>
      <h1>Focus</h1>
      <p>Pick a mode. Press play. Don&rsquo;t reach for your phone.</p>

      <section
        style={{
          marginTop: 'var(--space-6)',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 'var(--space-3)',
        }}
      >
        {MODE_ORDER.map((mode) => {
          const def = MODE_DEFINITIONS[mode];
          return (
            <button
              key={mode}
              type="button"
              onClick={() => onStart(mode)}
              style={{
                padding: 'var(--space-4)',
                background: 'var(--bg-elevated)',
                border: 'none',
                borderLeft: '2px solid var(--accent-warm)',
                color: 'var(--text)',
                borderRadius: 'var(--radius-sharp)',
                textAlign: 'left',
                cursor: 'pointer',
                fontFamily: 'var(--font-body)',
              }}
            >
              <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{def.label}</div>
              <div style={{ fontSize: '0.875rem', marginTop: 6, color: 'var(--text-muted)' }}>
                {def.description}
              </div>
            </button>
          );
        })}
      </section>

      <section style={{ marginTop: 'var(--space-8)' }}>
        <h2 style={{ fontSize: '1.125rem' }}>Recent sessions</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
          Your last 7 days will appear here once a session completes.
          Session history syncs to vaultbrain when EPIC-01 wires up;
          for now nothing&rsquo;s shown.
        </p>
      </section>
    </div>
  );
}
