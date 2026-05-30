/**
 * Lane A (Task A6) — Focus Hero full-screen active view.
 *
 * Countdown ring + phase label + pause/resume/abandon controls.
 * Confirms before abandoning. Toast notify on completion + abandon.
 *
 * Persistence callbacks (onStart / onComplete / onAbandon) wire to the
 * vaultbrain client at the App-level integration; left as TODOs here
 * until the integration commit lands.
 */

import { useEffect, useMemo, useState } from 'react';
import { useToast } from '@njz-os/ui';
import {
  MODE_DEFINITIONS,
  useFocusSession,
  type SessionMode,
} from '@njz-os/focus-engine';

export function FocusActive({
  mode,
  onExit,
}: {
  mode: SessionMode;
  onExit: () => void;
}) {
  const { notify } = useToast();
  const [started, setStarted] = useState(false);
  const fs = useFocusSession({
    initialMode: mode,
    onComplete: () => {
      notify('Session complete', { variant: 'success' });
    },
    onAbandon: () => {
      notify('Session abandoned', { variant: 'info' });
    },
  });

  useEffect(() => {
    if (!started) {
      fs.send({ kind: 'START', mode });
      setStarted(true);
    }
  }, [fs, mode, started]);

  useEffect(() => {
    if (fs.isComplete || fs.isAbandoned) {
      const id = setTimeout(onExit, 1_200);
      return () => clearTimeout(id);
    }
    return undefined;
  }, [fs.isComplete, fs.isAbandoned, onExit]);

  const def = MODE_DEFINITIONS[mode];
  const minutes = Math.floor(fs.secondsRemaining / 60);
  const seconds = fs.secondsRemaining % 60;
  const display = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  const ringStyle = useMemo<React.CSSProperties>(() => {
    const angle = fs.progressFraction * 360;
    const work = fs.phaseLabel === 'Work';
    const colour = work ? 'var(--accent-warm)' : 'var(--accent)';
    return {
      width: 240,
      height: 240,
      borderRadius: '50%',
      background: `conic-gradient(${colour} ${angle}deg, var(--bg-elevated) ${angle}deg)`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      transition: 'background 480ms ease',
    };
  }, [fs.progressFraction, fs.phaseLabel]);

  const onPauseOrResume = () => {
    if (fs.isRunning) fs.send({ kind: 'PAUSE' });
    else if (fs.isPaused) fs.send({ kind: 'RESUME' });
  };

  const onAbandon = () => {
    const ok = window.confirm(
      'End this session early? Your time so far won’t count toward your streak.'
    );
    if (ok) fs.send({ kind: 'ABANDON' });
  };

  const onComplete = () => fs.send({ kind: 'COMPLETE' });

  return (
    <div
      style={{
        minHeight: 'calc(100vh - 64px)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 'var(--space-6)',
      }}
    >
      <div
        aria-live="polite"
        style={{ fontSize: '0.875rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}
      >
        {def.label} · {fs.phaseLabel}
      </div>

      <div style={ringStyle} role="timer" aria-label={`${fs.phaseLabel} timer ${display} remaining`}>
        <div
          style={{
            width: 200,
            height: 200,
            borderRadius: '50%',
            background: 'var(--bg)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: 'var(--font-display)',
            fontSize: '3rem',
            fontWeight: 600,
            letterSpacing: '-0.02em',
          }}
        >
          {display}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
        <button
          type="button"
          onClick={onPauseOrResume}
          disabled={fs.isComplete || fs.isAbandoned}
          style={btnStyle('default')}
        >
          {fs.isPaused ? 'Resume' : 'Pause'}
        </button>
        <button
          type="button"
          onClick={onComplete}
          disabled={fs.isComplete || fs.isAbandoned}
          style={btnStyle('primary')}
        >
          Complete
        </button>
        <button
          type="button"
          onClick={onAbandon}
          disabled={fs.isComplete || fs.isAbandoned}
          style={btnStyle('danger')}
        >
          Abandon
        </button>
      </div>

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
        ← Back to focus home
      </button>
    </div>
  );
}

function btnStyle(variant: 'primary' | 'default' | 'danger'): React.CSSProperties {
  const base: React.CSSProperties = {
    padding: 'var(--space-3) var(--space-5)',
    borderRadius: 'var(--radius-sharp)',
    fontFamily: 'var(--font-body)',
    fontSize: '0.875rem',
    cursor: 'pointer',
    minWidth: 100,
  };
  if (variant === 'primary') {
    return { ...base, background: 'var(--accent)', color: 'var(--bg)', border: 'none' };
  }
  if (variant === 'danger') {
    return {
      ...base,
      background: 'transparent',
      color: 'var(--danger)',
      border: '1px solid var(--danger)',
    };
  }
  return {
    ...base,
    background: 'var(--bg-elevated)',
    color: 'var(--text)',
    border: 'none',
  };
}
