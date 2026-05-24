# tests/e2e/

Playwright end-to-end tests. Phase 1+.

## Phase 1 Targets

- Smoke: marketing site loads, webapp shell renders, all 7 module routes navigable.
- Full focus session: start → countdown → complete → see XP increment.
- Soundscape playback: start → audio plays → stop → state persisted.
- Distraction blocker: schedule → trigger → blocked URL redirected.

Configuration lands in `playwright.config.ts` once Phase 1 begins.
