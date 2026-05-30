[Ver001.000]

# PS-005 — Micro-Learning

- **Status:** Draft (Phase 0)
- **Owner:** Implementer (Phase 2)
- **Phase:** 2
- **Package:** `@njz-os/learning-cards`
- **Gate:** `G2.micro-learning`

## Purpose

Bite-sized visual card lessons inspired by Imprint's tap-forward format. Optimized for "micro-moments" — commutes, breaks, queueing. Drives Tertiary tier acquisition and Primary tier daily-habit reinforcement.

## Surface

```ts
import { createDeck, openCard, scheduleReview, type Card, type Deck } from '@njz-os/learning-cards';

const deck = await createDeck({ topic: 'feynman-technique', cards: 7 });
const next = openCard(deck);
scheduleReview(card, { easedQuality: 4 }); // SM-2
```

UI in `apps/web`:

- `/learn` — module home with deck library + new-card recommendations.
- `/learn/d/:deck` — deck reader (tap-forward).
- `/learn/review` — spaced-repetition review queue.

## Domain Types

- `Card`, `Deck`, `ReviewSchedule` (see SCHEMA_REGISTRY).

## Integration Points

- **Vaultbrain:** persist bookmarks, completion, SM-2 schedule per user.
- **PolyCo.World:** completed decks populate the Office Library; Memory Tomes unlocked from Brain Training games appear there too.
- **Focus Hero:** completing a deck during a focus session counts as a productive session.

## Risks

- **Content licensing.** Cards include illustrations + text from "world-class thinkers". Phase 2 ships only original content + clearly-attributed quotes. Mitigation: legal review pre-Phase-2.
- **Card quality at scale.** 500+ cards by Phase 4 — need editorial pipeline. Mitigation: community contribution model (Phase 3+) + maintained taxonomy.
- **Tap-forward feels shallow.** Mitigate by Connection Cards + Deep Dive types.

## Verification

- Unit: SM-2 schedule produces expected next-review intervals for canonical quality inputs.
- Unit: deck completion event fires correctly.
- Manual: 5-card deck on iPhone 12 renders without layout shift.

## Out of Scope (Phase 2)

- User-generated decks (Phase 3).
- Audio narration of cards (Phase 4).
- Translated decks (Phase 5 / i18n).

## References

- PRD §3.5.
- Imprint reference (PRD §3.5.1 citations).
- Content licensing decision: TBD ADR.

---

> **Implementation-ready expanded spec:** `docs/modules/micro-learning/EXPANDED.md`
