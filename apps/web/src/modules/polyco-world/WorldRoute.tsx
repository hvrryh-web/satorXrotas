/**
 * Lane C Task C6 + C7 — PolyCo.World Office route.
 *
 * Phase-1: renders the Office scene with a synthetic ProgressionEvent
 * stream so the user can preview decoration unlocks. Once Lane A's
 * vaultbrain wiring is in place, the synthetic stream gets replaced by
 * the live `useProgression` hook (PATCH-02 from PR #27).
 *
 * The packed PNG sprite atlas + Canvas 2D renderer are gated on the
 * asset pipeline (Task C1). This Phase-1 surface ships a schematic
 * CSS-grid view that consumes the same scene + unlock data the
 * production renderer will use, so the contract is real and the wiring
 * is just one swap when the atlas lands.
 */

import { useMemo, useState } from 'react';
import {
  parseScene,
  unlockedDecorations,
  type Decoration,
} from '@njz-os/polyworld';
import type { ProgressionEvent, UserId, SessionId } from '@njz-os/core';
import { OFFICE_SCENE } from './scenes/office';

const userId = 'u_demo' as UserId;
const sessionId = 's_demo' as SessionId;

function syntheticEvent(
  module:
    | 'focus-hero'
    | 'writing-space'
    | 'micro-learning'
    | 'brain-training',
  index: number
): ProgressionEvent {
  return {
    kind: 'session.complete',
    userId,
    sessionId,
    module,
    durationMs: 25 * 60_000,
    xpAwarded: 25,
    at: new Date(Date.now() - index * 60_000).toISOString(),
  };
}

function syntheticStreak(days: number): ProgressionEvent {
  return {
    kind: 'streak.extend',
    userId,
    module: 'focus-hero',
    newCurrent: days,
    at: new Date().toISOString(),
  };
}

const PALETTE = {
  floor: '#3F2E1F',
  wall: '#1E293B',
  door: '#92703E',
  unlocked: '#14B8A6',
};

export function WorldRoute() {
  const [focusCount, setFocusCount] = useState(0);
  const [writeCount, setWriteCount] = useState(0);
  const [learnCount, setLearnCount] = useState(0);
  const [trainCount, setTrainCount] = useState(0);
  const [streakDays, setStreakDays] = useState(0);

  const events = useMemo<ProgressionEvent[]>(() => {
    const list: ProgressionEvent[] = [];
    for (let i = 0; i < focusCount; i += 1) list.push(syntheticEvent('focus-hero', i));
    for (let i = 0; i < writeCount; i += 1) list.push(syntheticEvent('writing-space', i));
    for (let i = 0; i < learnCount; i += 1) list.push(syntheticEvent('micro-learning', i));
    for (let i = 0; i < trainCount; i += 1) list.push(syntheticEvent('brain-training', i));
    if (streakDays > 0) list.push(syntheticStreak(streakDays));
    return list;
  }, [focusCount, writeCount, learnCount, trainCount, streakDays]);

  const scene = useMemo(() => parseScene(OFFICE_SCENE, 'w_demo'), []);
  const unlocked = useMemo(() => unlockedDecorations(scene, events), [scene, events]);
  const unlockedIds = useMemo(() => new Set(unlocked.map((d: Decoration) => d.id)), [unlocked]);

  return (
    <div className="rat-page" style={{ maxWidth: 880 }}>
      <h1>PolyCo.World — Office</h1>
      <p>
        Your office grows as you build streaks across modules. Lane C ships
        the renderer + decoration unlocks; the asset pipeline + packed PNG
        sprite atlas arrive in a follow-up. For now this is a schematic
        view rendered from the same scene + unlock data the production
        renderer will consume.
      </p>

      <section style={{ marginTop: 'var(--space-6)' }}>
        <h2 style={{ fontSize: '1rem', marginBottom: 'var(--space-2)' }}>Office (8×8)</h2>
        <div
          aria-label="PolyCo.World Office schematic"
          style={{
            display: 'grid',
            gridTemplateColumns: `repeat(${scene.size[0]}, 1fr)`,
            gap: 2,
            background: 'var(--bg-elevated)',
            padding: 'var(--space-2)',
            borderRadius: 'var(--radius-sharp)',
            maxWidth: 480,
          }}
        >
          {scene.tiles.flatMap((row, ty) =>
            row.map((tile, tx) => {
              if (!tile) return <div key={`${tx}-${ty}`} style={{ aspectRatio: '1', background: 'transparent' }} />;
              const decorationHere = scene.decorations.find(
                (d) => d.position[0] === tx && d.position[1] === ty && unlockedIds.has(d.id)
              );
              const actorHere = scene.actors.find(
                (a) => a.position[0] === tx && a.position[1] === ty
              );
              const isFloor = tile.kind === 'floor';
              const isDoor = tile.kind === 'door';
              const background = decorationHere
                ? PALETTE.unlocked
                : isDoor
                  ? PALETTE.door
                  : isFloor
                    ? PALETTE.floor
                    : PALETTE.wall;
              return (
                <div
                  key={`${tx}-${ty}`}
                  title={
                    decorationHere
                      ? `${decorationHere.kind}: ${decorationHere.id} (unlocked)`
                      : actorHere
                        ? `actor: ${actorHere.id}`
                        : `${tile.kind}: ${tile.id}`
                  }
                  style={{
                    aspectRatio: '1',
                    background,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 10,
                    color: actorHere ? '#F8FAFC' : 'transparent',
                    fontWeight: actorHere ? 700 : undefined,
                  }}
                >
                  {actorHere ? '☆' : null}
                </div>
              );
            })
          )}
        </div>
        <p style={{ marginTop: 'var(--space-2)', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          {unlocked.length} of {scene.decorations.length} decorations unlocked
          (teal cells).
        </p>
      </section>

      <section
        style={{
          marginTop: 'var(--space-6)',
          padding: 'var(--space-4)',
          background: 'var(--bg-elevated)',
          borderRadius: 'var(--radius-sharp)',
        }}
      >
        <h2 style={{ fontSize: '1rem', marginTop: 0 }}>Synthetic progression (dev tool)</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          The sliders below feed a synthetic ProgressionEvent stream into
          the scene loader so you can preview which decorations unlock at
          which thresholds. When vaultbrain wiring lands these will be
          replaced by the live event stream from PATCH-02.
        </p>

        <Slider label="Focus sessions" value={focusCount} max={15} onChange={setFocusCount} />
        <Slider label="Writing sessions" value={writeCount} max={5} onChange={setWriteCount} />
        <Slider label="Micro-Learning sessions" value={learnCount} max={10} onChange={setLearnCount} />
        <Slider label="Brain-Training sessions" value={trainCount} max={10} onChange={setTrainCount} />
        <Slider label="Streak days" value={streakDays} max={14} onChange={setStreakDays} />
      </section>
    </div>
  );
}

function Slider({
  label,
  value,
  max,
  onChange,
}: {
  label: string;
  value: number;
  max: number;
  onChange: (v: number) => void;
}) {
  return (
    <div style={{ marginTop: 'var(--space-3)' }}>
      <label
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '0.85rem',
          marginBottom: 4,
        }}
      >
        {label}
        <strong>{value}</strong>
      </label>
      <input
        type="range"
        min={0}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{ width: '100%' }}
      />
    </div>
  );
}
