/**
 * Lane B Task B7 — Soundscapes home.
 *
 * Category tabs + the 5 baseline soundscapes filtered by current tab.
 * Picking a soundscape opens the active player.
 */

import { useState } from 'react';
import {
  BASELINE_SOUNDSCAPES,
  soundscapesByCategory,
  type Soundscape,
  type SoundscapeCategory,
} from '@njz-os/audio-engine';

const CATEGORIES: ReadonlyArray<{ id: SoundscapeCategory; label: string }> = [
  { id: 'focus', label: 'Focus' },
  { id: 'relax', label: 'Relax' },
  { id: 'sleep', label: 'Sleep' },
  { id: 'meditate', label: 'Meditate' },
];

const THEME_TINT: Record<string, string> = {
  nature: 'var(--success)',
  urban: 'var(--accent-warm)',
  cosmic: 'var(--accent)',
  minimal: 'var(--text-muted)',
  instrumental: 'var(--accent-warm)',
};

export function SoundHome({
  onSelect,
}: {
  onSelect: (s: Soundscape) => void;
}) {
  const [category, setCategory] = useState<SoundscapeCategory>('focus');
  const list = soundscapesByCategory(category, BASELINE_SOUNDSCAPES);

  return (
    <div className="rat-page" style={{ maxWidth: 880 }}>
      <h1>Soundscapes</h1>
      <p>
        Five baseline scapes ship with Phase 1. Custom builders + a Deep
        Canvas gallery arrive with the Premium tier.
      </p>

      <nav
        role="tablist"
        aria-label="Soundscape category"
        style={{
          display: 'flex',
          gap: 'var(--space-2)',
          marginTop: 'var(--space-6)',
          borderBottom: '1px solid var(--bg-elevated)',
        }}
      >
        {CATEGORIES.map((c) => {
          const isOn = c.id === category;
          return (
            <button
              key={c.id}
              type="button"
              role="tab"
              aria-selected={isOn}
              onClick={() => setCategory(c.id)}
              style={{
                background: 'transparent',
                border: 'none',
                padding: 'var(--space-3) var(--space-4)',
                color: isOn ? 'var(--text)' : 'var(--text-muted)',
                borderBottom: `2px solid ${isOn ? 'var(--accent)' : 'transparent'}`,
                cursor: 'pointer',
                fontSize: '0.95rem',
                fontFamily: 'var(--font-body)',
              }}
            >
              {c.label}
            </button>
          );
        })}
      </nav>

      <section
        style={{
          marginTop: 'var(--space-6)',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 'var(--space-3)',
        }}
      >
        {list.length === 0 && (
          <p style={{ color: 'var(--text-muted)' }}>
            No baseline soundscape in this category yet — more arrive next
            wave.
          </p>
        )}
        {list.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => onSelect(s)}
            style={{
              padding: 'var(--space-4)',
              background: 'var(--bg-elevated)',
              border: 'none',
              borderLeft: `2px solid ${THEME_TINT[s.theme] ?? 'var(--accent)'}`,
              color: 'var(--text)',
              borderRadius: 'var(--radius-sharp)',
              textAlign: 'left',
              cursor: 'pointer',
              fontFamily: 'var(--font-body)',
            }}
          >
            <div style={{ fontSize: '1rem', fontWeight: 600 }}>{s.title}</div>
            <div style={{ fontSize: '0.8rem', marginTop: 6, color: 'var(--text-muted)' }}>
              {s.theme} · {Math.round(s.durationMs / 60_000)} min loop
            </div>
            {s.binauralPresetId && (
              <div style={{ fontSize: '0.75rem', marginTop: 8, color: 'var(--accent)' }}>
                Binaural overlay · {s.binauralPresetId}
              </div>
            )}
          </button>
        ))}
      </section>
    </div>
  );
}
