# @njz-os/focus-engine

Focus session state machines + distraction-blocker types.

## Surface (Phase 0 stubs)

- `session` — `FocusSession`, `SessionMode`
- `blocker` — `BlockerSettings`, `BlockSchedule`, `BlockAttempt`, `EnforcementLevel`

## Phase 1 Implementation

XState-driven state machine for pomodoro / deep-work cycles. Local-first timing (no server in the countdown loop). Vaultbrain persistence on boundaries (start, pause, resume, complete, abandon).

See `docs/prototype-systems/PS-001-focus-hero.md` and `PS-003-distraction-blocker.md`.

## ADR

ADR-0007 (state machine design) before unlock of `G1.focus-hero`.
