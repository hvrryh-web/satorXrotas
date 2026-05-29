[Ver001.000]

# PS-006 — Brain Training

- **Status:** Draft (Phase 0)
- **Owner:** Implementer (Phase 2)
- **Phase:** 2
- **Package:** `@njz-os/analytics` (Cognitive Profile + scoring) + per-game modules in `apps/web/src/modules/brain-training/games/*`
- **Gate:** `G2.brain-training`

## Purpose

Five cognitive games at launch (Stroop, Corsi Blocks, Digit Span, Memory Matrix, Match Pairs) targeting cognitive flexibility, visuospatial memory, verbal memory, pattern recognition, and processing speed respectively. Plus the *My Journey* adaptive progression system.

## Surface

```ts
import { CognitiveProfile, scoreSession, suggestWorkout } from '@njz-os/analytics';

const profile: CognitiveProfile = await loadProfile(userId);
const session = await runGame('stroop-test', { difficulty: 'auto' });
const updated = scoreSession(profile, session);
const tomorrow = suggestWorkout(updated); // 3-game plan
```

UI in `apps/web`:

- `/train` — module home (Today's Workout + game library + profile radar).
- `/train/game/:gameId` — game runner.
- `/train/journey` — My Journey chapter view.

## Domain Types

- `CognitiveProfile`, `Percentile`, `WorkoutPlan` (`@njz-os/analytics`).
- Per-game session records — typed under each game module.

## Integration Points

- **Vaultbrain:** persist profile, session records, journey progress.
- **Progression:** game completions emit XP events.
- **PolyCo.World:** workout completion produces Neural Dust; chapter completion adds a wing to the Dojo.
- **Focus Hero:** brain training XP boosts hero progression rate.
- **Soundscapes:** "Focus Now" can include a quick brain training warm-up (configurable).

## Risks

- **Game design quality.** Five games is the floor; if any feels broken, retention dies. Mitigation: game designer review before each game ships; user-test cohort.
- **Cognitive Profile validity.** Five-dimension vector is a simplification of real cognition. Mitigation: clear "for self-tracking, not diagnostic" messaging.
- **Adaptive engine over/under-corrects.** ±15% difficulty change per session can feel jarring. Mitigation: dampen with rolling 7-session window; cap per-day adjustment.
- **Comparison cohorts.** Percentiles need a baseline. Mitigation: bootstrap with population data from public neuropsychology references; refine with first-1000-user cohort.

## Verification

- Unit: each game's scoring function is deterministic for fixed seed.
- Unit: adaptive engine doesn't oscillate (no >30% swing within 5 sessions).
- E2E: complete a daily workout; verify XP grant + profile vector update.

## Out of Scope (Phase 2)

- Cross-user leaderboards (Phase 3).
- Game expansion past five (Phase 3+).
- Clinical-grade assessment positioning (never; we're educational, not diagnostic).
- Wearable input (heart rate, EEG) — speculative, Phase 5+.

## References

- PRD §3.1.
- Reference research: Lumosity (60+ games), CogniFit (Corsi Span standard), Impulse (quick-workout format).
- ADR-0007 (focus engine — shared state machine patterns).

---

> **Expanded spec:** queued for a future session per the next-stages plan; will appear under `docs/modules/<module>/EXPANDED.md` once the Phase-2 documentation sprint runs.
