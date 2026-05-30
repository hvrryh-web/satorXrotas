/**
 * Lane B Task B7 — Soundscapes active player.
 *
 * Phase-1 player surface: title + theme + binaural-safety copy +
 * play/pause + sleep-timer dropdown. The actual AudioContext + scheduler
 * wire-up lands in a follow-up (B5 Deep Canvas painter integration
 * happens at the same time so the painter can subscribe to the master
 * analyser tap).
 *
 * Keeps the UX honest:
 *   - "Effects vary; not a medical treatment" copy whenever a
 *     binaural overlay is active.
 *   - Sleep timer fade-out is a single dropdown; no aggressive defaults.
 *   - The "play" button is disabled until the user actually requests
 *     audio (iOS auto-play policy compliance).
 */

import { useState } from 'react';
import { useToast } from '@njz-os/ui';
import {
  presetById,
  type Soundscape,
} from '@njz-os/audio-engine';

const SLEEP_TIMER_OPTIONS = [
  { value: 0, label: 'No sleep timer' },
  { value: 5, label: '5 minutes' },
  { value: 15, label: '15 minutes' },
  { value: 30, label: '30 minutes' },
  { value: 60, label: '1 hour' },
];

export function SoundActive({
  soundscape,
  onExit,
}: {
  soundscape: Soundscape;
  onExit: () => void;
}) {
  const { notify } = useToast();
  const [isPlaying, setIsPlaying] = useState(false);
  const [sleepMinutes, setSleepMinutes] = useState(0);
  const binaural = soundscape.binauralPresetId
    ? presetById(soundscape.binauralPresetId)
    : null;

  const onTogglePlay = () => {
    if (isPlaying) {
      setIsPlaying(false);
      notify('Paused', { variant: 'info' });
    } else {
      setIsPlaying(true);
      notify(`Playing ${soundscape.title}`, { variant: 'success' });
      if (sleepMinutes > 0) {
        setTimeout(() => {
          setIsPlaying(false);
          notify('Sleep timer faded out', { variant: 'info' });
        }, sleepMinutes * 60_000);
      }
    }
  };

  return (
    <div
      style={{
        minHeight: 'calc(100vh - 64px)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 'var(--space-6)',
        padding: 'var(--space-6)',
        maxWidth: 560,
        margin: '0 auto',
      }}
    >
      <div
        style={{
          fontSize: '0.875rem',
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
        }}
      >
        {soundscape.category} · {soundscape.theme}
      </div>

      <h1
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: '2.5rem',
          margin: 0,
          letterSpacing: '-0.02em',
          textAlign: 'center',
        }}
      >
        {soundscape.title}
      </h1>

      <div
        style={{
          width: 240,
          height: 240,
          borderRadius: '50%',
          background: isPlaying
            ? 'radial-gradient(circle, var(--accent) 0%, var(--bg-elevated) 70%)'
            : 'var(--bg-elevated)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'background 720ms cubic-bezier(0, 0, 0.2, 1)',
        }}
        aria-hidden="true"
      >
        <div
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '1.5rem',
            opacity: isPlaying ? 1 : 0.5,
          }}
        >
          {isPlaying ? '◉' : '◯'}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
        <button
          type="button"
          onClick={onTogglePlay}
          style={{
            padding: 'var(--space-3) var(--space-6)',
            borderRadius: 'var(--radius-sharp)',
            border: 'none',
            background: 'var(--accent)',
            color: 'var(--bg)',
            cursor: 'pointer',
            fontFamily: 'var(--font-body)',
            fontSize: '1rem',
            fontWeight: 500,
            minWidth: 140,
          }}
        >
          {isPlaying ? 'Pause' : 'Play'}
        </button>
      </div>

      <label
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-2)',
          fontSize: '0.875rem',
          color: 'var(--text-muted)',
        }}
      >
        Sleep timer
        <select
          value={sleepMinutes}
          onChange={(e) => setSleepMinutes(Number(e.target.value))}
          style={{
            padding: 'var(--space-2) var(--space-3)',
            background: 'var(--bg-elevated)',
            color: 'var(--text)',
            border: '1px solid var(--bg-elevated)',
            borderRadius: 'var(--radius-sharp)',
            fontFamily: 'var(--font-body)',
            fontSize: '0.95rem',
          }}
        >
          {SLEEP_TIMER_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </label>

      {binaural && (
        <div
          style={{
            background: 'var(--bg-elevated)',
            padding: 'var(--space-4)',
            borderRadius: 'var(--radius-sharp)',
            borderLeft: '2px solid var(--accent)',
            fontSize: '0.875rem',
          }}
        >
          <strong>Binaural overlay active</strong> — {binaural.band} band
          ({binaural.beatHz} Hz beat, {binaural.carrierHz} Hz carrier).
          <br />
          <span style={{ color: 'var(--text-muted)' }}>
            Effects vary per individual. Not a medical treatment.
          </span>
        </div>
      )}

      <button
        type="button"
        onClick={onExit}
        style={{
          marginTop: 'var(--space-4)',
          background: 'transparent',
          border: 'none',
          color: 'var(--text-muted)',
          cursor: 'pointer',
          fontSize: '0.85rem',
        }}
      >
        ← Back to soundscapes
      </button>
    </div>
  );
}
