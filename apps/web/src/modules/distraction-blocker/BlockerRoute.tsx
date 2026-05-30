/**
 * Lane D Task D3 + D6 — Distraction Blocker module entry.
 *
 * Phase-1 surface:
 *   - 7 block-list category toggles (compiled into a host deny-list)
 *   - Custom host input (wildcard via prefix * for subdomains)
 *   - Enforcement-level picker with per-tier behaviour preview
 *   - Focus-sync toggle (arm/disarm a focus-sync schedule)
 *   - Compiled deny-list preview (read-only) so users see what the
 *     SW would block
 *
 * SW registration (Task D2) + Chrome MV3 extension (Task D4) +
 * calendar OAuth (Task D5) queued for follow-ups.
 */

import { useMemo, useState } from 'react';
import {
  computeFocusScore,
  type EnforcementLevel,
} from '@njz-os/focus-engine';
import {
  BLOCK_CATEGORIES,
  compileBlockHosts,
} from './categories';

const ENFORCEMENT_LEVELS: ReadonlyArray<{
  id: EnforcementLevel;
  label: string;
  description: string;
}> = [
  {
    id: 'gentle',
    label: 'Gentle',
    description: 'Soft nudge — interstitial with a 5-second pause; click-through allowed.',
  },
  {
    id: 'moderate',
    label: 'Moderate',
    description: 'Interstitial + cooldown 60 s; 3 overrides per day.',
  },
  {
    id: 'strict',
    label: 'Strict',
    description: 'Hard block during scheduled windows; no overrides.',
  },
  {
    id: 'maximum',
    label: 'Maximum',
    description: 'Maximum focus mode — even the override toggle hidden.',
  },
];

export function BlockerRoute() {
  const [enabledCategories, setEnabledCategories] = useState<Set<string>>(new Set());
  const [customHostInput, setCustomHostInput] = useState('');
  const [customHosts, setCustomHosts] = useState<string[]>([]);
  const [enforcement, setEnforcement] = useState<EnforcementLevel>('moderate');
  const [focusSyncArmed, setFocusSyncArmed] = useState(false);

  const compiledHosts = useMemo(
    () => compileBlockHosts(enabledCategories, customHosts),
    [enabledCategories, customHosts]
  );

  const toggleCategory = (id: string) => {
    const next = new Set(enabledCategories);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setEnabledCategories(next);
  };

  const addCustomHost = () => {
    const host = customHostInput.trim().replace(/^https?:\/\//, '').replace(/\/.*$/, '');
    if (!host) return;
    if (customHosts.includes(host)) return;
    setCustomHosts([...customHosts, host]);
    setCustomHostInput('');
  };

  const removeCustomHost = (host: string) => {
    setCustomHosts(customHosts.filter((h) => h !== host));
  };

  return (
    <div className="rat-page" style={{ maxWidth: 880 }}>
      <h1>Distraction Blocker</h1>
      <p>
        Block the sites that pull you out of focus. Phase-1 ships the
        in-app block list + focus-sync coupling. The Chrome extension
        (cross-origin enforcement) and calendar integration follow.
      </p>

      <section style={{ marginTop: 'var(--space-6)' }}>
        <h2 style={{ fontSize: '1.125rem' }}>Categories</h2>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: 'var(--space-3)',
          }}
        >
          {BLOCK_CATEGORIES.map((c) => {
            const isOn = enabledCategories.has(c.id);
            return (
              <button
                key={c.id}
                type="button"
                onClick={() => toggleCategory(c.id)}
                aria-pressed={isOn}
                style={{
                  padding: 'var(--space-3)',
                  background: isOn ? 'var(--danger)' : 'var(--bg-elevated)',
                  color: isOn ? 'var(--bg)' : 'var(--text)',
                  border: 'none',
                  borderRadius: 'var(--radius-sharp)',
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-body)',
                }}
              >
                <div style={{ fontWeight: 600 }}>{c.label}</div>
                <div style={{ fontSize: '0.8rem', marginTop: 4, opacity: 0.85 }}>
                  {c.description}
                </div>
                <div style={{ fontSize: '0.7rem', marginTop: 6, opacity: 0.7 }}>
                  {c.hosts.length} hosts · {isOn ? 'BLOCKING' : 'allowed'}
                </div>
              </button>
            );
          })}
        </div>
      </section>

      <section style={{ marginTop: 'var(--space-6)' }}>
        <h2 style={{ fontSize: '1.125rem' }}>Custom hosts</h2>
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <input
            type="text"
            value={customHostInput}
            onChange={(e) => setCustomHostInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addCustomHost()}
            placeholder="example.com or *.example.com"
            style={{
              flex: 1,
              padding: 'var(--space-2) var(--space-3)',
              background: 'var(--bg-elevated)',
              color: 'var(--text)',
              border: '1px solid var(--bg-elevated)',
              borderRadius: 'var(--radius-sharp)',
              fontFamily: 'var(--font-body)',
            }}
          />
          <button
            type="button"
            onClick={addCustomHost}
            style={{
              padding: 'var(--space-2) var(--space-4)',
              background: 'var(--accent)',
              color: 'var(--bg)',
              border: 'none',
              borderRadius: 'var(--radius-sharp)',
              cursor: 'pointer',
            }}
          >
            Add
          </button>
        </div>
        {customHosts.length > 0 && (
          <ul
            style={{
              listStyle: 'none',
              padding: 0,
              marginTop: 'var(--space-3)',
              display: 'flex',
              flexWrap: 'wrap',
              gap: 'var(--space-2)',
            }}
          >
            {customHosts.map((h) => (
              <li
                key={h}
                style={{
                  padding: '4px 10px',
                  background: 'var(--bg-elevated)',
                  borderRadius: 'var(--radius-sharp)',
                  fontSize: '0.85rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                {h}
                <button
                  type="button"
                  onClick={() => removeCustomHost(h)}
                  aria-label={`Remove ${h}`}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                  }}
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section style={{ marginTop: 'var(--space-6)' }}>
        <h2 style={{ fontSize: '1.125rem' }}>Enforcement level</h2>
        <div role="radiogroup" aria-label="Enforcement level" style={{ display: 'grid', gap: 'var(--space-2)' }}>
          {ENFORCEMENT_LEVELS.map((l) => {
            const isOn = enforcement === l.id;
            return (
              <button
                key={l.id}
                type="button"
                role="radio"
                aria-checked={isOn}
                onClick={() => setEnforcement(l.id)}
                style={{
                  padding: 'var(--space-3)',
                  background: 'var(--bg-elevated)',
                  border: `1px solid ${isOn ? 'var(--accent)' : 'transparent'}`,
                  color: 'var(--text)',
                  borderRadius: 'var(--radius-sharp)',
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-body)',
                }}
              >
                <div style={{ fontWeight: 600 }}>{l.label}</div>
                <div style={{ fontSize: '0.85rem', marginTop: 4, color: 'var(--text-muted)' }}>
                  {l.description}
                </div>
              </button>
            );
          })}
        </div>
        <p style={{ marginTop: 'var(--space-3)', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          Sample focus score (5 attempted distractions at {enforcement}):{' '}
          <strong>{computeFocusScore(5, enforcement)}</strong>.
        </p>
      </section>

      <section style={{ marginTop: 'var(--space-6)' }}>
        <h2 style={{ fontSize: '1.125rem' }}>Focus-sync</h2>
        <label
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-3)',
            padding: 'var(--space-3)',
            background: 'var(--bg-elevated)',
            borderRadius: 'var(--radius-sharp)',
          }}
        >
          <input
            type="checkbox"
            checked={focusSyncArmed}
            onChange={(e) => setFocusSyncArmed(e.target.checked)}
          />
          <span>
            <strong>Auto-arm during focus sessions.</strong>{' '}
            <span style={{ color: 'var(--text-muted)' }}>
              When on, every Focus Hero session activates the block list
              for its duration. Wires to the FocusSession state machine
              once Lane A vaultbrain integration lands.
            </span>
          </span>
        </label>
      </section>

      <section style={{ marginTop: 'var(--space-6)' }}>
        <h2 style={{ fontSize: '1.125rem' }}>Compiled deny-list ({compiledHosts.length})</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          This is what the in-app service worker will redirect when the
          block list is armed. Add categories or custom hosts above to
          grow it.
        </p>
        {compiledHosts.length === 0 ? (
          <p style={{ color: 'var(--text-muted)' }}>No hosts enabled.</p>
        ) : (
          <pre
            style={{
              background: 'var(--bg-elevated)',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-sharp)',
              fontSize: '0.85rem',
              maxHeight: 240,
              overflow: 'auto',
            }}
          >
            {compiledHosts.join('\n')}
          </pre>
        )}
      </section>
    </div>
  );
}
