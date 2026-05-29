[Ver001.000]

# Focus Hero — Expanded Module Documentation

> **Lane A** in Stage 3 of the next-stages plan. Implementation-ready spec
> for the next agent picking up this lane.

## 1. Module identity & scope

| Field | Value |
|-------|-------|
| **Module name** | Focus Hero |
| **Slug (code)** | `focus-hero` |
| **Status** | Documented (Accepted); implementation pending Phase-D code execution |
| **Owner role** | Implementer |
| **Channel** | `packages-engines` + `web-app` |
| **Gate protected** | `G1.focus-hero` (currently LOCKED) |
| **Phase** | 1 |
| **Source ADRs** | ADR-0009 (Focus Engine state machine — XState v5) |
| **Source PS** | `docs/prototype-systems/PS-001-focus-hero.md` |
| **Parent docs** | `MASTER_PLAN.md`, `docs/product/PRD.md` §3.1.3 + §3.1 (Focus Hero overlays), `docs/product/PERSONAS.md` (Balanced Achiever) |
| **Plan reference** | Lane A in `.agents/session-workplans/SW-20260524-stage-3-lanes.md` |

Focus Hero is the **first user-visible RAT-OS feature** and the daily anchor
for the Balanced Achiever and Creative Professional personas. It wraps four
documented session modes — `pomodoro_25_5` (25/5), `deep_work_50_10` (50/10),
`sprint_15_3` (15/3), and `flow_90_20` (90/20) — in a single XState v5
state machine with React bindings and a full-screen UI surface. The
machine is the local source of truth; vaultbrain persists progress at
session boundaries; PolyCo.World subscribes to the resulting
ProgressionEvents to unlock decorations.

The implementation must satisfy three structural properties:

1. **State survives device sleeps, tab backgrounding, and cross-device
   handoffs.** Countdown remaining time is *always* re-derived from
   `Date.now() - startedAt - pausedDuration` on every animation frame.
   No `setInterval` is the source of truth.
2. **Persistence is at session boundaries only.** Network writes
   exclusively on `START`, `COMPLETE`, and `ABANDON`. No per-tick, no
   pause/resume hits — these are pure local state changes.
3. **Anti-cheat enforced server-side.** Sessions shorter than a
   mode-specific `min_session_ms` (default 60 s, 30 s for sprint) do not
   award XP. This defeats "1-second pomodoro" streak abuse.

## 2. Architecture

```
apps/web/src/modules/focus-hero/
  ├─ FocusRoute.tsx        ─┐  Routes (was PhaseStub; replaced)
  ├─ Home.tsx              ─┘
  ├─ Active.tsx
  ├─ HistoryList.tsx
  └─ components/
       ├─ ModeTile.tsx
       ├─ CountdownRing.tsx
       ├─ PhaseLabel.tsx
       └─ SessionControls.tsx
                 │
                 │ consumes via React hook
                 ▼
packages/@njz-os/focus-engine/src/
  ├─ machine.ts            XState v5 setup({}) actor
  ├─ react.ts              useFocusSession hook
  ├─ session.ts            (existing) types
  ├─ blocker.ts            (existing) types (Lane D's territory)
  └─ persistence.ts        Vaultbrain boundary actor
                 │
                 │ (boundary actions only)
                 ▼
packages/adapters/vaultbrain-client/  → vaultbrain (upstream, Phase 1 stub)
```

Key trade-offs already decided (ADR-0009 §"Decision"):

- XState v5 chosen over hand-rolled reducer / Zustand for formal
  state-graph + typed actors + replay tooling.
- Timestamp-based countdown re-derivation chosen over `setInterval` tick
  loops — eliminates background-tab throttling drift.
- Persistence boundaries are work-state changes only — no PAUSE/RESUME
  network traffic.

Architecture extensions needed for implementation (not in the ADR):

- `useSyncExternalStore` for cross-tab consistency of the active
  session — two tabs viewing the same user must see identical countdown.
- Offline queue for vaultbrain boundary actions when the network is
  unavailable; flush on reconnect. The vaultbrain-client adapter is a
  stub in Phase 0 — Lane A's persistence layer must either inject a
  mock adapter (for tests) or accept the NOT_IMPLEMENTED error and queue
  the event locally.

## 3. Domain types & contracts

### Types introduced or extended in `@njz-os/focus-engine`

```ts
// packages/@njz-os/focus-engine/src/session.ts (existing, extend)
import type { SessionId, UserId } from '@njz-os/core';

export type SessionMode =
  | 'pomodoro_25_5'
  | 'deep_work_50_10'
  | 'sprint_15_3'
  | 'flow_90_20';

export type SessionPhase = 'work' | 'break';

export interface SessionModeConfig {
  workDurationMs: number;
  breakDurationMs: number;
  minSessionMs: number; // anti-cheat floor
  displayName: string;
  description: string;
}

export const MODE_CONFIGS: Record<SessionMode, SessionModeConfig> = {
  pomodoro_25_5:  { workDurationMs: 25*60_000, breakDurationMs:  5*60_000, minSessionMs: 60_000, displayName: 'Pomodoro 25/5',   description: '25 min work · 5 min break' },
  deep_work_50_10:{ workDurationMs: 50*60_000, breakDurationMs: 10*60_000, minSessionMs: 60_000, displayName: 'Deep Work 50/10', description: '50 min work · 10 min break' },
  sprint_15_3:    { workDurationMs: 15*60_000, breakDurationMs:  3*60_000, minSessionMs: 30_000, displayName: 'Sprint 15/3',     description: '15 min work · 3 min break' },
  flow_90_20:     { workDurationMs: 90*60_000, breakDurationMs: 20*60_000, minSessionMs: 60_000, displayName: 'Flow 90/20',      description: '90 min flow · 20 min recovery' },
};

export interface FocusSession {
  id: SessionId;
  userId: UserId;
  mode: SessionMode;
  startedAt: string;       // ISO 8601
  durationMs: number;      // accumulated work time, excluding pauses
  pausedDurationMs: number;
  state: 'pending' | 'running' | 'paused' | 'completed' | 'abandoned';
  phase: SessionPhase;
}
```

### Machine context + events (from ADR-0009 §"Machine shape", expanded)

```ts
// packages/@njz-os/focus-engine/src/machine.ts (new)
import { setup, assign, fromPromise } from 'xstate';

type Context = {
  sessionId: SessionId;
  userId: UserId;
  mode: SessionMode;
  startedAt: number;     // Date.now() at the most recent run-start
  elapsedMs: number;     // accumulated across pauses
  pausedAt: number | null;
  pausedDurationMs: number;
  workDurationMs: number;
  breakDurationMs: number;
  phase: SessionPhase;
};

type Events =
  | { type: 'START' }
  | { type: 'PAUSE' }
  | { type: 'RESUME' }
  | { type: 'COMPLETE' }
  | { type: 'ABANDON' }
  | { type: 'TICK' }
  | { type: 'PHASE_END' };

export const focusMachine = setup({
  types: {} as { context: Context; events: Events },
  actors: {
    persistStart:    fromPromise<void, { sessionId: SessionId; mode: SessionMode }>(async (_input) => { /* injected */ }),
    persistComplete: fromPromise<void, { sessionId: SessionId; durationMs: number }>(async (_input) => { /* injected */ }),
    persistAbandon:  fromPromise<void, { sessionId: SessionId }>(async (_input) => { /* injected */ }),
  },
}).createMachine({
  id: 'focus',
  initial: 'pending',
  context: ({ input }) => /* see §4 walkthrough */,
  states: {
    pending: {
      on: { START: { target: 'running.work', actions: 'recordStart' } },
    },
    running: {
      initial: 'work',
      on: {
        PAUSE: { target: 'paused', actions: 'recordPauseAt' },
        ABANDON: { target: 'abandoning' },
      },
      states: {
        work:  { on: { PHASE_END: 'break' } },
        break: { on: { PHASE_END: '#focus.completing' } },
      },
    },
    paused: {
      on: {
        RESUME: { target: 'running', actions: 'accumulatePausedDuration' },
        ABANDON: { target: 'abandoning' },
      },
    },
    completing: { invoke: { src: 'persistComplete', onDone: 'completed' } },
    abandoning: { invoke: { src: 'persistAbandon', onDone: 'abandoned' } },
    completed: { type: 'final' },
    abandoned: { type: 'final' },
  },
});
```

### React hook surface

```ts
// packages/@njz-os/focus-engine/src/react.ts (new)
export interface UseFocusSessionResult {
  state: 'pending' | 'running' | 'paused' | 'completed' | 'abandoned';
  phase: SessionPhase;
  secondsRemaining: number;     // re-derived from Date.now() each rAF
  progressFraction: number;     // 0..1 within current phase
  send: (event: Events) => void;
}

export function useFocusSession(mode: SessionMode): UseFocusSessionResult;
```

### Cross-package contracts consumed

| From | Type / function | Purpose |
|------|-----------------|---------|
| `@njz-os/core/src/identity.ts` | `UserId`, `SessionId` | brand types |
| `@njz-os/core/src/progression.ts` | `ProgressionEvent` union | emitted to vaultbrain bus |
| `@njz-os/progression/src/index.ts` | `applyEvent(state, event)` | reducer used in tests to verify reducer-equivalence after machine emit |
| `packages/adapters/vaultbrain-client` | `createVaultbrainClient` + `publish<P>(event)` | persistence actor; in Phase 1 returns NOT_IMPLEMENTED, machine queues |

### Vaultbrain endpoints called (per ADR-0008 surface, currently pending upstream)

| Method | Path | When |
|--------|------|------|
| POST | `/sessions/start` | machine enters `running.work` from `pending` |
| POST | `/sessions/{id}/complete` | machine enters `completed` |
| POST | `/sessions/{id}/abandon` | machine enters `abandoned` |

Each returns a `Session` (per `contracts/openapi/njz-rat-os.yaml`). The
client adapter must handle 5xx with exponential-backoff retry and a
local-queue fallback (the queued mutation is flushed on next online
event).

## 4. Implementation walkthrough — task by task

Per the lane To-Do in SW-20260524 (Tasks A1–A8). Each task is one PR
commit. Subtasks become commit-shape work; the task lands when all
universal criteria green.

### Task A1 — Install XState v5 and scaffold `machine.ts`

```bash
pnpm --filter @njz-os/focus-engine add xstate @xstate/react
pnpm --filter @njz-os/focus-engine add -D @statelyai/inspect # dev-only
```

Create `packages/@njz-os/focus-engine/src/machine.ts`:

```ts
import { setup } from 'xstate';
export const focusMachine = setup({}).createMachine({ id: 'focus' });
```

Then re-export from `src/index.ts`. Verify `pnpm typecheck` green.
Commit: `feat(focus): scaffold XState v5 machine`.

### Task A2 — Implement the state graph per ADR-0009

Translate the §3 machine shape into `machine.ts`. Key details:

- `setup({...})` declares `types`, `actions`, `actors`, `guards` as
  named entries before `createMachine({...})` references them by string.
- Each `running.work` and `running.break` substate registers a
  `TICK` handler that internally re-computes `secondsRemaining`
  from context — *not* via `after`. We use a custom `effect` (via an
  external rAF loop in `useFocusSession`) to send `TICK` events, not
  XState `after`, because `after` is duration-based and would drift.
- `PHASE_END` is computed externally by the rAF loop:
  `secondsRemaining <= 0 ? send('PHASE_END') : send('TICK')`.

Add a Vitest snapshot test:

```ts
import { focusMachine } from '../src/machine';
import { fromObservable } from 'xstate';

test('state graph matches ADR-0009', () => {
  expect(focusMachine.getStateNodes()).toMatchSnapshot();
});
```

Commit: `feat(focus): implement state graph per ADR-0009`.

### Task A3 — Wire vaultbrain persistence boundary actions

Add `src/persistence.ts`:

```ts
import { fromPromise } from 'xstate';
import type { VaultbrainClient } from '@njz-os/adapters-vaultbrain-client';

export function makePersistenceActors(client: VaultbrainClient) {
  return {
    persistStart: fromPromise(async ({ input }: { input: { sessionId; mode } }) => {
      await client.publish({ kind: 'session.start', /* ... */ });
    }),
    persistComplete: fromPromise(async ({ input }) => {
      await client.publish({ kind: 'session.complete', /* ... */ });
    }),
    persistAbandon: fromPromise(async ({ input }) => {
      await client.publish({ kind: 'session.abandon', /* ... */ });
    }),
  };
}
```

The machine consumes these via `setup({ actors: ... })`. In tests,
inject a mock client that records calls. In production, the real client
will currently throw `VaultbrainError('NOT_IMPLEMENTED')` — wrap each
actor in a try/catch and append failures to a local-queue (Phase 1
acceptable: queue in memory; Phase 2 persists queue to IndexedDB).

Tests verify: START → 1 publish; PAUSE/RESUME/TICK → 0 publishes;
COMPLETE → 1 publish; ABANDON → 1 publish (no XP).

Commit: `feat(focus): wire vaultbrain persistence on boundaries`.

### Task A4 — React bindings (`useFocusSession`)

Add `src/react.ts`:

```tsx
import { useActor } from '@xstate/react';
import { useSyncExternalStore, useRef, useEffect } from 'react';
import { focusMachine } from './machine';
import { MODE_CONFIGS, type SessionMode } from './session';

export function useFocusSession(mode: SessionMode) {
  const [snapshot, send] = useActor(focusMachine, { input: { mode } });

  // External rAF loop drives TICK + PHASE_END; never uses setInterval.
  useEffect(() => {
    let raf = 0;
    const loop = () => {
      const remaining = computeRemaining(snapshot.context);
      if (remaining <= 0) send({ type: 'PHASE_END' });
      else send({ type: 'TICK' });
      raf = requestAnimationFrame(loop);
    };
    if (snapshot.matches('running')) raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [snapshot, send]);

  return {
    state: snapshot.value as 'pending' | 'running' | 'paused' | 'completed' | 'abandoned',
    phase: snapshot.context.phase,
    secondsRemaining: Math.max(0, Math.floor(computeRemaining(snapshot.context) / 1000)),
    progressFraction: 1 - computeRemaining(snapshot.context) /
      (snapshot.context.phase === 'work' ? snapshot.context.workDurationMs : snapshot.context.breakDurationMs),
    send,
  };
}

function computeRemaining(ctx) {
  const elapsed = Date.now() - ctx.startedAt - ctx.pausedDurationMs;
  const phaseDur = ctx.phase === 'work' ? ctx.workDurationMs : ctx.breakDurationMs;
  return phaseDur - elapsed;
}
```

Unit test the hook against a mocked machine snapshot; assert
`secondsRemaining` decreases monotonically and reaches 0 at the phase
boundary.

Commit: `feat(focus): add useFocusSession React hook`.

### Task A5 — Module home UI (`Home.tsx`)

Replace `apps/web/src/modules/focus-hero/FocusRoute.tsx` `PhaseStub` with:

```tsx
import { ModeTile } from './components/ModeTile';
import { HistoryList } from './HistoryList';
import { MODE_CONFIGS } from '@njz-os/focus-engine';
import { Link } from 'react-router-dom';

export function FocusRoute() {
  return (
    <section className="rat-page">
      <h1>Focus Hero</h1>
      <p>Pick a mode and start a session.</p>
      <div className="focus-mode-grid">
        {Object.entries(MODE_CONFIGS).map(([mode, cfg]) => (
          <ModeTile key={mode} mode={mode} config={cfg} to={`/focus/active?mode=${mode}`} />
        ))}
      </div>
      <h2>Recent sessions</h2>
      <HistoryList userId={/* from auth context */} />
    </section>
  );
}
```

`ModeTile` is a `Link` with title + duration. `HistoryList` is a stub
that fetches the last 7 completed sessions and shows a streak heat-map
(see §5 telemetry).

Commit: `feat(web/focus): module home with mode picker + history`.

### Task A6 — Active session full-screen view (`Active.tsx`)

```tsx
import { useFocusSession } from '@njz-os/focus-engine';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { CountdownRing } from './components/CountdownRing';
import { SessionControls } from './components/SessionControls';

export function ActiveRoute() {
  const [params] = useSearchParams();
  const mode = (params.get('mode') ?? 'pomodoro_25_5') as SessionMode;
  const session = useFocusSession(mode);
  const nav = useNavigate();

  useEffect(() => {
    if (session.state === 'pending') session.send({ type: 'START' });
    if (session.state === 'completed' || session.state === 'abandoned') {
      setTimeout(() => nav('/focus'), 2000);
    }
  }, [session.state]);

  return (
    <section className="focus-active">
      <CountdownRing seconds={session.secondsRemaining} progress={session.progressFraction} phase={session.phase} />
      <h2 aria-live="polite">{session.phase === 'work' ? 'Focus' : 'Break'}</h2>
      <SessionControls
        onPause={() => session.send({ type: 'PAUSE' })}
        onResume={() => session.send({ type: 'RESUME' })}
        onAbandon={() => /* confirm dialog */ session.send({ type: 'ABANDON' })}
        state={session.state}
      />
    </section>
  );
}
```

The confirm dialog on abandon uses a native `<dialog>` element for a11y
(or a focus-trapping React modal if preferred). The countdown ring is a
`<svg>` with a `<circle>` whose `strokeDasharray` reflects
`progressFraction`.

Commit: `feat(web/focus): active session full-screen view`.

### Task A7 — Tests + accessibility

Unit tests (Vitest):

- `machine.test.ts`: every transition; pause/resume sums correctly; abandon
  short-of-min produces no XP event; clock injection (via `setSystemTime`
  if Vitest's `vi.useFakeTimers()`) advances state.
- `react.test.tsx`: `useFocusSession` snapshot reaches 0 at boundary.
- `persistence.test.ts`: boundary actors fire exactly once on
  START/COMPLETE/ABANDON; nothing on PAUSE/RESUME/TICK.

E2E (Playwright):

```ts
// tests/e2e/focus-session.spec.ts (placeholder; full impl when Playwright installed)
import { test, expect } from '@playwright/test';

test.skip('completes a full pomodoro_25_5 cycle', async ({ page }) => {
  await page.clock.install({ time: new Date('2026-05-25T10:00:00Z') });
  await page.goto('/focus/active?mode=pomodoro_25_5');
  await page.clock.fastForward('25:00');
  await expect(page.getByText('Break')).toBeVisible();
  await page.clock.fastForward('5:00');
  await expect(page).toHaveURL(/\/focus$/);
});
```

A11y audit (acceptance gates for §6):

- Keyboard: Tab traverses all controls; Enter activates; Esc opens
  abandon confirm.
- ARIA: `aria-live="polite"` on phase label; `role="timer"` on countdown.
- Focus ring: visible on every interactive element.
- Reduced motion: `prefers-reduced-motion: reduce` disables the ring's
  rotation animation.

Commit: `test(focus): unit + E2E placeholder + a11y baseline`.

### Task A8 — Flip `G1.focus-hero` to OPEN (orchestrator-only)

This task is reserved for the orchestrator's Phase-E review per the plan.
The subagent must **not** touch `.agents/PHASE_GATES.md`.

The orchestrator verifies all A1–A7 PRs green, then in a tiny follow-up
PR:

- Flip the row in `.agents/PHASE_GATES.md` from LOCKED to OPEN with
  date stamp.
- Append `.agents/DECISION_LOG.md`:
  `YYYY-MM-DD | @hvrryh-web | gate | Opened G1.focus-hero per Lane A merge → ADR-0009 satisfied`.
- Append `.agents/phase-logbooks/PHASE-1-LOGBOOK.md` with a
  one-paragraph entry referencing the lane PR.

## 5. Telemetry & analytics events

### Events emitted by Focus Hero (canonical via `contracts/events/progression-events.json`)

| Event `kind` | When | Payload fields | Routed to |
|--------------|------|----------------|-----------|
| `session.start` | machine: `pending → running.work` | `userId`, `sessionId`, `module: 'focus-hero'`, `mode`, `at` | vaultbrain `progression_events` |
| `session.complete` | machine: `running.* → completed` (post-persistComplete) | + `durationMs`, `xpAwarded` | vaultbrain |
| `session.abandon` | machine: `* → abandoned` | (no XP) | vaultbrain |
| `streak.extend` | server-side: new daily session in current streak | `userId`, `module: 'focus-hero'`, `newCurrent`, `at` | vaultbrain |
| `streak.break` | server-side: 48h gap with no session | `userId`, `module: 'focus-hero'`, `at` | vaultbrain |

### XP formula (Phase 1)

```
xpAwarded = floor(
  baseXP[mode]                              // 10 / 25 / 5 / 50 for pomodoro/deep/sprint/flow
  × (durationMs / workDurationMs[mode])     // fractional credit if user completed less than full
  × streakBonus                              // 1.0 .. 1.5 in 7-day banding
)
```

Anti-cheat: `durationMs < MODE_CONFIGS[mode].minSessionMs` ⇒ `xpAwarded = 0`.

### Mapping to OKRs

Per `docs/product/OKRS.md`:

- **O1.1 KR3** (5K MAU end of Month 2) → tracked via session.start cohort + DAU/MAU rollup.
- **O1.1 KR4** (D7 ≥ 18%) → tracked via streak.extend at the 7-day band.
- **O2.2** (free→paid conversion) — indirect; sustained sessions imply premium-receptive cohort.

Lane A does **not** instrument session-quality metrics (focus-score,
phase-completion ratio per mode) in Phase 1 — those are Phase 2 analytics
(per PS-001 §3.1.4).

## 6. Test plan

| Tier | Tooling | Target | Owner |
|------|---------|--------|-------|
| Unit | Vitest | ≥ 90% line coverage on `machine.ts` + `persistence.ts` + `react.ts` | Implementer |
| Integration | Vitest + msw | adapter-boundary behaviour: NOT_IMPLEMENTED → local-queue → flush on reconnect | Implementer |
| E2E | Playwright | one full `pomodoro_25_5` cycle with clock injection | Implementer |
| Cross-tab | Playwright (multi-page) | two tabs of /focus/active?mode=X show identical countdown | Critic (lane reviewer) |
| a11y | @axe-core/playwright | zero critical violations on `/focus` + `/focus/active` | Implementer |
| Perf | Lighthouse (CI) | ≥ 85 perf on `/focus`; FCP < 1.5 s on a mid-range mobile | Platform |

Test fixtures:

- `test/fixtures/session-mocks.ts` — canned `VaultbrainClient` mock that
  records publish calls.
- `test/fixtures/clock.ts` — `Date.now` patcher tied to Vitest's
  `vi.setSystemTime`.

## 7. Accessibility plan (WCAG 2.2 AA)

Per-component a11y checklist:

| Component | Requirement | How verified |
|-----------|-------------|--------------|
| `ModeTile` | Keyboard-focusable, Enter triggers Link, visible focus ring | manual + axe |
| `CountdownRing` | `role="timer"`, `aria-label="Time remaining in focus phase"`, updates announced via `aria-live="polite"` parent label | manual |
| `PhaseLabel` | `aria-live="polite"` so phase transitions are announced | manual |
| `SessionControls` | Buttons named via `aria-label`; Esc opens abandon dialog | manual |
| Abandon dialog | Native `<dialog>` with focus trap; Esc closes; Enter on Confirm submits | manual + axe |
| Reduced motion | `@media (prefers-reduced-motion: reduce)` disables ring rotation; phase label still announces | manual |
| Color contrast | Phase label text ≥ 4.5:1 against background per ROOT_AXIOMS PR-02 | axe |

Non-goals (Phase 2):

- Screen-reader-only deep-work mode summaries.
- Haptic feedback on mobile phase transitions.
- Voice-controlled session start.

## 8. Risk register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Clock drift in background tab causes wrong-feeling countdown | M | M | Timestamp-based re-derivation (decided in ADR-0009); cross-tab test catches regression |
| Cross-device handoff feels "jumpy" when vaultbrain returns stale state | M | M | Local-first; vaultbrain reconciles on next event, not on read |
| User abandons just under `min_session_ms`, expects partial XP | M | L | Surface the threshold in UI: "Sessions under 1 min don't count toward streaks" |
| Vaultbrain adapter remains NOT_IMPLEMENTED through Phase 1 launch | M | H | Lane A's persistence layer queues locally and flushes on online — works even without vaultbrain. Lane F upstream PR (#118) lands eventually |
| XState bundle size (≈ 40 KB gz) feels heavy | L | L | Defer until Phase-2 perf audit; lazy-load `/focus/active` route |
| Streak abuse via system-clock manipulation | L | M | Phase 1: trust the client (we're not insurance). Phase 3: corroborate server-side using session count per day |

## 9. Cross-lane handoffs

| Direction | What | Consumer/Producer | Contract |
|-----------|------|-------------------|----------|
| **Emits** ProgressionEvents (`session.start/.complete/.abandon`) | Lane C consumes for PolyCo Office decoration unlocks | event payloads per `contracts/events/progression-events.json` |
| **Emits** "active session started" signal | Lane D's `focus-sync` blocker schedule subscribes via `useFocusSession` | hook return value `state === 'running'` |
| **Consumes** auth state | Lane E's `AuthProvider` supplies `userId` via context | `useAuth().userId` |
| **Consumes** soundscape pairing toggle | Lane B's audio engine: when user opts into coupling, calling `useFocusSession` also starts the chosen soundscape via `audio-engine` | optional integration in `Active.tsx`; not blocking |
| **Consumes** schema | `@njz-os/core` `ProgressionEvent` discriminated union | re-exported via `@njz-os/focus-engine` for app consumers |

Lane A's outputs are stable contracts — Lane C, D, E can begin parallel
work against these shapes even if Lane A is in flight.

## 10. Out of scope (this module / phase)

- Hero RPG progression beyond XP (skill trees, abilities, gear) — Phase 2+.
- Voice-controlled session start / hands-free mode — Phase 4.
- Apple Watch / Wear OS surfaces — Phase 3.
- Server-side anti-cheat beyond min-session enforcement — Phase 3.
- Multi-user collaborative focus (shared timer, shared streak) —
  Phase 3 per PS-001 "Out of Scope".
- Cognitive-Profile updates from focus sessions (focus-session-derived
  cognitive metrics live in PS-006 Brain Training scoring, not here).

## 11. Open questions / TODOs for implementation

| Question | Options | Recommended default | Decision owner |
|----------|---------|---------------------|-----------------|
| Should `flow_90_20` allow mid-session re-pomodoro break (25 min in)? | (a) strict 90/20 only (b) configurable | (a) strict for Phase 1; add (b) in Phase 2 | Architect |
| Should TICK fire at 1 Hz or 60 Hz (rAF)? | (a) 1 Hz `setInterval` (b) rAF every frame (c) 1 Hz emulated via rAF | (c) — re-render only when integer seconds change; rAF drives boundary check | Implementer |
| How does pause behave with `flow_90_20`? Should breaks pause too? | (a) only work pauses (b) any phase pauses | (b) — uniform behaviour | Architect (micro-ADR if changes) |
| Where does the offline-queue live? | (a) memory (b) IndexedDB | (a) Phase 1; (b) Phase 2 — log as ADR-0015 candidate when implementing | Implementer |
| Should `Home.tsx` show today's progress vs goal? | (a) yes (b) defer to onboarding-step-3 goals lane | (a) thin version reading from `useAuth().weeklyGoal` (Lane E ships goal) | Designer |
| `useFocusSession` re-mounts when user navigates between routes — should session persist? | (a) module-level store (b) pause-on-navigate (c) full-screen-only mode | (a) — wrap with a context provider at the route level so navigating away doesn't end the session | Implementer |

Each "Implementer" decision is local — record in `.agents/DECISION_LOG.md` and pass on. Each "Architect" or "Designer" decision merits a tiny follow-up ADR if non-trivial.

---

> **When implementing**, follow `ROOT_AXIOMS/03_PROCEDURES/01-add-a-module-package.md` for module-package conventions. **Do NOT** touch `.agents/PHASE_GATES.md` — that's orchestrator territory in Task A8.

> **See also:** ADR-0009, PS-001, `contracts/events/progression-events.json`, `packages/@njz-os/core/src/progression.ts`, `apps/web/src/shared/gates.ts`, `apps/web/src/shared/PhaseStub.tsx`.
