[Ver001.000]

# PS-001 — Focus Hero

- **Status:** Draft (Phase 0); flips to Approved when ADR-0007 lands.
- **Owner:** Implementer (Phase 1)
- **Phase:** 1
- **Package:** `@njz-os/focus-engine` + apps/web module
- **Gate:** `G1.focus-hero`

## Purpose

Gamified focus timer. The webapp's daily anchor for the Balanced Achiever and Creative Professional tiers. Wraps pomodoro / deep-work sessions with XP, streaks, hero progression, and PolyCo.World decoration unlocks.

## Surface

Module API (consumed by `apps/web/src/modules/focus-hero/`):

```ts
import { createFocusSession, type SessionMode } from '@njz-os/focus-engine';

const session = createFocusSession({ mode: 'pomodoro_25_5', userId });
session.start();
session.subscribe((state) => render(state));
session.pause();
session.complete();
```

UI surface in `apps/web`:

- `/focus` — module home with quick-start, session history, streak heat map.
- `/focus/active` — full-screen running session UI.

## Domain Types

See `.agents/SCHEMA_REGISTRY.md`:

- `FocusSession`, `SessionMode` (`@njz-os/focus-engine/src/session.ts`)
- `StreakState`, `XpTotals`, `ProgressionEvent` (`@njz-os/core/src/progression.ts`)

## Integration Points

- **Vaultbrain:** persist `FocusSession` on start/complete/abandon; subscribe for cross-device state.
- **Progression package:** emits `ProgressionEvent` on session boundaries; routes to XP totals and streak update.
- **PolyCo.World:** session completion triggers decoration unlock checks (`@njz-os/polyworld` consumes via event bus).
- **Soundscapes:** "Focus Now" button starts a focus session + a focus soundscape concurrently.
- **Distraction Blocker:** active focus session can auto-trigger a blocker block window (opt-in).
- **Brain Training:** completing a daily workout grants XP that boosts hero progression rate.

## Risks

- **Drift between client clock and server time.** Pause/resume across device switches risks state confusion. Mitigation: timestamp-based, not duration-based, state machine; server reconciliation on reconnect.
- **Background tab throttling.** Browsers throttle `setInterval` in background; countdown can drift. Mitigation: re-derive remaining time from `Date.now() - startedAt` each animation frame.
- **Streak abuse.** Users might game streaks (1-second sessions). Mitigation: minimum session duration enforced server-side before XP grant.

## Verification

- Unit tests on state machine transitions (start → run → pause → resume → complete; start → run → abandon).
- Integration test: cross-device sync — Device A starts session, Device B sees state within 2 seconds.
- E2E test: complete a full pomodoro; verify XP increment + decoration unlock event.
- Manual smoke: 25 min × 5 cycles without drift > 2 seconds.

## Out of Scope (Phase 1)

- Multi-user collaborative focus (Phase 3 — see PS-007).
- Hero RPG combat or skill trees (not a goal; we're "RPG-flavored", not an RPG).
- Voice control / hands-free start.
- Apple Watch / Wear OS surfaces.

## References

- PRD §3.1, §3.3 (Focus Training + Blocker integration).
- ADR-0007 (Focus engine design — TBD before Phase 1 unlocks).
- `@njz-os/focus-engine/README.md`.

---

> **Implementation-ready expanded spec:** `docs/modules/focus-hero/EXPANDED.md`
