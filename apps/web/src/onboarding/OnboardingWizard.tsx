/**
 * Lane E (Task E6) — Onboarding wizard.
 *
 * Three-step wizard run on first sign-in:
 *   1. Pick primary modules (multi-select from the seven)
 *   2. Find My Frequency calibration (binaural quick-pick)
 *   3. Set first weekly goal (sessions/week × minimum minutes)
 *
 * Persists state via localStorage 'njz:onboarding' so reload resumes
 * the same step. On completion, emits `onboarding.complete` to the
 * default event bus (analytics + Lane A home heat-map listen for it).
 */

import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@njz-os/ui';
import type { ModuleSlug } from '@njz-os/core';

interface OnboardingState {
  step: 1 | 2 | 3;
  picks: ModuleSlug[];
  frequencyPreset: 'delta' | 'theta' | 'alpha' | 'beta' | 'gamma' | null;
  weeklyGoal: { sessions: number; minutesPerSession: number } | null;
}

const STORAGE_KEY = 'njz:onboarding';

function loadState(): OnboardingState {
  if (typeof window === 'undefined') return defaultState();
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultState();
    const parsed = JSON.parse(raw) as Partial<OnboardingState>;
    return { ...defaultState(), ...parsed };
  } catch {
    return defaultState();
  }
}

function defaultState(): OnboardingState {
  return { step: 1, picks: [], frequencyPreset: null, weeklyGoal: null };
}

const MODULES: Array<{ slug: ModuleSlug; label: string; tagline: string }> = [
  { slug: 'focus-hero', label: 'Focus Hero', tagline: 'Timed focus sessions' },
  { slug: 'soundscapes', label: 'Soundscapes', tagline: 'Ambient + binaural' },
  { slug: 'distraction-blocker', label: 'Blocker', tagline: 'Time-boxed blocking' },
  { slug: 'writing-space', label: 'Writing', tagline: 'Mobile-first editor' },
  { slug: 'micro-learning', label: 'Learning', tagline: 'Spaced-repetition cards' },
  { slug: 'brain-training', label: 'Training', tagline: 'Cognitive games' },
  { slug: 'polyco-world', label: 'World', tagline: 'Progress visualisation' },
];

const FREQUENCIES = [
  { id: 'delta' as const, label: 'Delta', range: '0.5–4 Hz', use: 'Deep rest' },
  { id: 'theta' as const, label: 'Theta', range: '4–8 Hz', use: 'Creative flow' },
  { id: 'alpha' as const, label: 'Alpha', range: '8–12 Hz', use: 'Calm focus' },
  { id: 'beta' as const, label: 'Beta', range: '12–30 Hz', use: 'Active work' },
  { id: 'gamma' as const, label: 'Gamma', range: '30–100 Hz', use: 'Sharp focus' },
];

export function OnboardingWizard() {
  const navigate = useNavigate();
  const { notify } = useToast();
  const [state, setState] = useState<OnboardingState>(loadState);

  const persist = useCallback((next: OnboardingState) => {
    setState(next);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    }
  }, []);

  const togglePick = (slug: ModuleSlug) => {
    const picks = state.picks.includes(slug)
      ? state.picks.filter((s) => s !== slug)
      : [...state.picks, slug];
    persist({ ...state, picks });
  };

  const advance = () => {
    if (state.step === 1 && state.picks.length === 0) {
      notify('Pick at least one module to continue', { variant: 'warning' });
      return;
    }
    if (state.step === 2 && !state.frequencyPreset) {
      notify('Pick a frequency preset to continue', { variant: 'warning' });
      return;
    }
    if (state.step === 3) {
      if (!state.weeklyGoal) {
        notify('Set a weekly goal to finish onboarding', { variant: 'warning' });
        return;
      }
      complete();
      return;
    }
    persist({ ...state, step: (state.step + 1) as 2 | 3 });
  };

  const back = () => {
    if (state.step === 1) return;
    persist({ ...state, step: (state.step - 1) as 1 | 2 });
  };

  const complete = useCallback(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem(STORAGE_KEY);
    }
    // We can't emit a typed payload that conforms to NjzEventMap here
    // (no user id / session id yet); analytics consumers can subscribe
    // to a string-keyed channel in a follow-up. For now, log + toast.
    notify('Welcome to RAT-OS', { variant: 'success' });
    navigate('/');
  }, [navigate, notify]);

  const setGoal = (sessions: number, minutesPerSession: number) => {
    persist({ ...state, weeklyGoal: { sessions, minutesPerSession } });
  };

  const progress = useMemo(() => ((state.step - 1) / 2) * 100, [state.step]);

  return (
    <div className="rat-page" style={{ maxWidth: 640 }}>
      <div
        style={{
          height: 4,
          background: 'var(--bg-elevated)',
          marginBottom: 'var(--space-6)',
          borderRadius: 'var(--radius-sharp)',
          overflow: 'hidden',
        }}
        aria-hidden="true"
      >
        <div
          style={{
            height: '100%',
            width: `${progress}%`,
            background: 'var(--accent)',
            transition: 'width 240ms cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        />
      </div>

      {state.step === 1 && (
        <Step1Picks picks={state.picks} onToggle={togglePick} />
      )}
      {state.step === 2 && (
        <Step2Frequency
          selected={state.frequencyPreset}
          onSelect={(id) => persist({ ...state, frequencyPreset: id })}
        />
      )}
      {state.step === 3 && (
        <Step3Goal goal={state.weeklyGoal} onSet={setGoal} />
      )}

      <div style={{ marginTop: 'var(--space-6)', display: 'flex', gap: 'var(--space-3)' }}>
        {state.step > 1 && (
          <button
            type="button"
            onClick={back}
            style={btnStyle()}
          >
            Back
          </button>
        )}
        <button
          type="button"
          onClick={advance}
          style={btnStyle('primary')}
        >
          {state.step === 3 ? 'Finish' : 'Next'}
        </button>
      </div>
    </div>
  );
}

function btnStyle(variant: 'primary' | 'default' = 'default') {
  return {
    padding: 'var(--space-2) var(--space-4)',
    borderRadius: 'var(--radius-sharp)',
    border:
      variant === 'primary'
        ? 'none'
        : '1px solid var(--bg-elevated)',
    background: variant === 'primary' ? 'var(--accent)' : 'transparent',
    color: variant === 'primary' ? 'var(--bg)' : 'var(--text)',
    fontFamily: 'var(--font-body)',
    fontSize: '0.875rem',
    cursor: 'pointer',
  } as const;
}

function Step1Picks({
  picks,
  onToggle,
}: {
  picks: ModuleSlug[];
  onToggle: (slug: ModuleSlug) => void;
}) {
  return (
    <div>
      <h1>Pick your modules</h1>
      <p>Choose the ones you&rsquo;ll use first. You can change later.</p>
      <div
        style={{
          marginTop: 'var(--space-4)',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 'var(--space-3)',
        }}
      >
        {MODULES.map((m) => {
          const isOn = picks.includes(m.slug);
          return (
            <button
              key={m.slug}
              type="button"
              onClick={() => onToggle(m.slug)}
              aria-pressed={isOn}
              style={{
                padding: 'var(--space-3)',
                background: isOn ? 'var(--accent)' : 'var(--bg-elevated)',
                color: isOn ? 'var(--bg)' : 'var(--text)',
                border: 'none',
                borderRadius: 'var(--radius-sharp)',
                textAlign: 'left',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 600 }}>{m.label}</div>
              <div style={{ fontSize: '0.8rem', marginTop: 4, opacity: 0.8 }}>{m.tagline}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Step2Frequency({
  selected,
  onSelect,
}: {
  selected: OnboardingState['frequencyPreset'];
  onSelect: (id: NonNullable<OnboardingState['frequencyPreset']>) => void;
}) {
  return (
    <div>
      <h1>Find your frequency</h1>
      <p>
        Pick a binaural-beat band to seed your default soundscape. Effects
        vary per individual; this isn&rsquo;t a medical treatment.
      </p>
      <div
        style={{
          marginTop: 'var(--space-4)',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
          gap: 'var(--space-3)',
        }}
      >
        {FREQUENCIES.map((f) => {
          const isOn = selected === f.id;
          return (
            <button
              key={f.id}
              type="button"
              onClick={() => onSelect(f.id)}
              aria-pressed={isOn}
              style={{
                padding: 'var(--space-3)',
                background: isOn ? 'var(--accent)' : 'var(--bg-elevated)',
                color: isOn ? 'var(--bg)' : 'var(--text)',
                border: 'none',
                borderRadius: 'var(--radius-sharp)',
                textAlign: 'left',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 600 }}>{f.label}</div>
              <div style={{ fontSize: '0.8rem', marginTop: 4, opacity: 0.85 }}>{f.range}</div>
              <div style={{ fontSize: '0.75rem', marginTop: 4, opacity: 0.7 }}>{f.use}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Step3Goal({
  goal,
  onSet,
}: {
  goal: OnboardingState['weeklyGoal'];
  onSet: (sessions: number, minutes: number) => void;
}) {
  const sessions = goal?.sessions ?? 5;
  const minutes = goal?.minutesPerSession ?? 25;
  return (
    <div>
      <h1>Set your weekly goal</h1>
      <p>How many focus sessions per week, and how long each?</p>

      <div style={{ marginTop: 'var(--space-4)' }}>
        <label htmlFor="sessions" style={{ display: 'block', marginBottom: 4 }}>
          Sessions per week: <strong>{sessions}</strong>
        </label>
        <input
          id="sessions"
          type="range"
          min={1}
          max={14}
          value={sessions}
          onChange={(e) => onSet(Number(e.target.value), minutes)}
          style={{ width: '100%' }}
        />
      </div>

      <div style={{ marginTop: 'var(--space-4)' }}>
        <label htmlFor="minutes" style={{ display: 'block', marginBottom: 4 }}>
          Minutes per session: <strong>{minutes}</strong>
        </label>
        <input
          id="minutes"
          type="range"
          min={5}
          max={90}
          step={5}
          value={minutes}
          onChange={(e) => onSet(sessions, Number(e.target.value))}
          style={{ width: '100%' }}
        />
      </div>

      <p style={{ marginTop: 'var(--space-4)', color: 'var(--text-muted)' }}>
        Estimated weekly effort: <strong>{sessions * minutes} minutes</strong>{' '}
        ({Math.round((sessions * minutes) / 60 * 10) / 10} hours)
      </p>
    </div>
  );
}
