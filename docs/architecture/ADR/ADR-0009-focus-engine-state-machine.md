[Ver001.000]

# ADR-0009 — Focus Engine State Machine (XState v5)

- **Status:** Accepted
- **Date:** 2026-05-24
- **Deciders:** @hvrryh-web
- **Tags:** focus, state-machine, xstate, focus-hero
- **Protects gate:** `G1.focus-hero`

## Context

The Focus Hero module needs a precise, testable state machine for focus sessions that:

- Survives device sleeps, tab backgrounding, and cross-device handoffs without drifting.
- Models all four documented session modes from the PRD (§3.1.2 derivatives + Focus Hero):
  - `pomodoro_25_5` — 25 min work / 5 min break
  - `deep_work_50_10` — 50 min work / 10 min break
  - `sprint_15_3` — 15 min sprint / 3 min break
  - `flow_90_20` — 90 min flow block / 20 min recovery
- Emits `ProgressionEvent`s at session boundaries (per `contracts/events/progression-events.json`).
- Integrates cleanly with `packages/adapters/vaultbrain-client` for persistence (per ADR-0008) and with `@njz-os/audio-engine` for optional soundscape coupling.

The bootstrap stub at `packages/@njz-os/focus-engine/src/session.ts` only declares the `FocusSession` and `SessionMode` types. The runtime model is undefined.

Three runtime options were considered:

1. Hand-rolled `useReducer` state machine inside React components.
2. Zustand store with explicit transition functions.
3. **XState v5** — declarative state machine with formal verification, typed actors, and a React binding (`@xstate/react`).

## Decision

Use **XState v5** as the state-machine engine for Focus Hero, with the following structure:

### Machine shape

```ts
// packages/@njz-os/focus-engine/src/machine.ts
import { setup } from 'xstate';
import type { FocusSession, SessionMode } from './session';

type Context = {
  sessionId: SessionId;
  userId: UserId;
  mode: SessionMode;
  startedAt: number;     // Date.now() at most recent run-start
  elapsedMs: number;     // accumulated across pauses
  pausedAt: number | null;
  workDurationMs: number;
  breakDurationMs: number;
  phase: 'work' | 'break';
};

type Events =
  | { type: 'START' }
  | { type: 'PAUSE' }
  | { type: 'RESUME' }
  | { type: 'COMPLETE' }
  | { type: 'ABANDON' }
  | { type: 'TICK' }
  | { type: 'PHASE_END' };
```

States: `pending → running → (paused | running) → completed | abandoned`. A `running` state has child states `work` and `break`; `PHASE_END` transitions between them; final `COMPLETE` exits.

### Drift handling

Countdown remaining time is **always re-derived from `Date.now() - startedAt - pausedDuration`** on every animation frame and on every event. No `setInterval` is the source of truth. This eliminates background-tab throttling drift.

### Pause/Resume semantics

`PAUSE` captures `pausedAt = Date.now()` and stops the visual timer. `RESUME` adds `(Date.now() - pausedAt)` to `pausedDuration` and clears `pausedAt`. The machine is timestamp-based, never duration-based.

### Persistence boundaries

The machine emits side-effect actions at exactly these transitions; each translates to a single vaultbrain call:

| Transition | Adapter call | Event emitted |
|------------|--------------|---------------|
| `pending → running (START)` | `POST /sessions/start` | `session.start` |
| `running → completed (COMPLETE)` | `POST /sessions/{id}/complete` | `session.complete` |
| `running → abandoned (ABANDON)` | `POST /sessions/{id}/abandon` | `session.abandon` |

`PAUSE` / `RESUME` / `TICK` / `PHASE_END` do **not** hit the network — they're local state changes only. Phase transitions are reconstructable from `started_at + duration + phase` on the server side.

### React binding

`packages/@njz-os/focus-engine/src/react.ts` exports `useFocusSession(mode)` — wraps `@xstate/react`'s `useMachine`, returns `{ state, send, secondsRemaining, phase, progressFraction }`. UI components (`apps/web/src/modules/focus-hero/`) consume only this hook; they never touch the machine directly.

### Anti-cheat (minimum session duration)

Server-side: `POST /sessions/{id}/complete` rejects sessions shorter than `min_session_ms` for that mode (default 60 s, except `sprint_15_3` which allows 30 s). Client can still complete instantly but no XP is granted. Documented as a deliberate constraint to defeat "1-second pomodoro" streak abuse.

## Consequences

**Positive:**

- Formal state model is testable in isolation (Vitest + `@statelyai/inspect` snapshots).
- Background-tab and device-sleep behaviour is correct by construction.
- Persistence boundaries are explicit; no accidental over-fetching.
- Pattern reusable for `@njz-os/audio-engine` session machines later.
- XState's typed actors give us end-to-end type safety from machine to React props.

**Negative:**

- XState adds bundle weight (~40 KB gzipped for `xstate` + `@xstate/react`). Acceptable for a webapp; non-trivial for a future widget surface (`apps/desktop-widget`).
- Learning curve for contributors unfamiliar with state-machine declarative syntax. Mitigated by keeping the machine small (< 200 LOC target).
- XState v5 is newer than v4; community examples skew older. Mitigated by following the official docs and pinning a stable minor.

**Neutral:**

- The machine itself runs in any JavaScript environment. The widget can adopt the same machine if it imports `@njz-os/focus-engine` without React bindings.

## Alternatives Considered

- **Hand-rolled `useReducer` machine.** Cheaper bundle, but loses formal verification, replay tooling, and typed actor composition. Rejected: complexity grows fast with phase transitions + pause/resume + persistence side effects.
- **Zustand store with imperative transitions.** Good for UI state, but lacks the explicit state-graph that pause/resume semantics demand. Rejected for this domain; we still use Zustand for ephemeral UI elsewhere (per CLAUDE.md).
- **Robot or `@hookstate/core`.** Lighter weight but smaller community + less mature React story. Rejected on ecosystem grounds.
- **Worker-based tick loop.** Tempting for cross-tab consistency, but Web Workers can't reliably persist state across page reloads. Rejected; timestamp-based reconstruction solves the same problem more simply.

## Related

- ADR-0008 — Vaultbrain integration shape (persistence target for this machine).
- `docs/prototype-systems/PS-001-focus-hero.md` — module spec.
- `packages/@njz-os/focus-engine/src/session.ts` — type stubs to be elaborated.
- `contracts/events/progression-events.json` — event taxonomy this machine emits.
- `.agents/SCHEMA_REGISTRY.md` — `FocusSession`, `SessionMode` registered.

---

> When proposing, leave Status: Proposed. On approval, change to Accepted in a follow-up commit.
> Append a one-line entry to `.agents/DECISION_LOG.md` referencing this ADR.
