# @njz-os/progression

Pure-function XP / streak / reward calculus. No I/O; persistence delegated to the vaultbrain adapter.

## Surface

- `ProgressionState` — combined XP + streak snapshot per user
- `applyEvent(state, event)` — fold `ProgressionEvent` over state (reducer-style)
- `emptyXpTotals()` — initial XP record across all module slugs

## Why Pure

Progression must be deterministic and replayable from the event log. No randomness, no time-of-call dependence beyond what the event carries.
