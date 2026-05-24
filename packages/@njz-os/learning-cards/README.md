# @njz-os/learning-cards

Micro-learning card data model + spaced-repetition scheduler.

## Surface (Phase 0 stubs)

- `card` — `Card`
- `deck` — `Deck`, `DeckKind`
- `spaced-repetition` — `ReviewSchedule`, `Quality`

## Phase 2 Implementation

SM-2 algorithm for spaced repetition. Card renderer (tap-forward) lives in `apps/web/src/modules/micro-learning/`.

See `docs/prototype-systems/PS-005-micro-learning.md`.
