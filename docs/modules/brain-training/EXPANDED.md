[Ver001.000]

# Brain Training — Expanded Module Documentation

> **Phase-2 B'** in the Stage 3 documentation sprint continuation.
> Implementation-ready spec for the next agent picking up Brain Training.

## 1. Module identity & scope

| Field | Value |
|-------|-------|
| **Module name** | Brain Training (5 games + Cognitive Profile + My Journey) |
| **Slug (code)** | `brain-training` |
| **Status** | Documented (Accepted); implementation pending Phase 2 |
| **Owner role** | Implementer + Designer (game UX) + Critic (cognitive-validity review) |
| **Channel** | `packages-engines` + `web-app` |
| **Gate protected** | `G2.brain-training` (currently LOCKED; opens after Phase 1 exit per `docs/product/OKRS.md`) |
| **Phase** | 2 (5 baseline games at launch) → Phase 3+ adds games 6+ |
| **Source ADRs** | **None Phase-1**. Recommends new ADR-0018 (adaptive-difficulty engine — ±15 % bounded, rolling-window, anti-oscillation) and ADR-0019 (cognitive-profile baseline population — bootstrap source for percentile cohorts). See §11 |
| **Source PS** | `docs/prototype-systems/PS-006-brain-training.md` |
| **Parent docs** | PRD §3.1 (Focus Training Module — game catalogue), MARKET_REVIEW.md (Lumosity 60+ games; CogniFit Corsi Span standard; Impulse quick-workout), PERSONAS.md (Primary tier morning cognitive warm-up) |
| **Plan reference** | Stage 3 continuation per `.agents/handoff/stage-3-doc-expansion-next-session.md` |

Brain Training is the **cognitive-conditioning surface** and one of the
two highest-converting categories in the wellness-productivity market
(6–9 % freemium → paid, per MARKET_REVIEW.md vs 3–5 % industry baseline).
Five games at Phase-2 launch covering five cognitive domains, plus the
*My Journey* adaptive progression system that guides users through
chapters with personalised daily workouts.

The five Phase-2 games (PRD §3.1.2):

| Game | Cognitive domain | Session length |
|------|-------------------|----------------|
| Stroop Test | Cognitive flexibility, selective attention, response inhibition | 3–5 min |
| Corsi Blocks | Visuospatial working memory, spatial reasoning | 4–6 min |
| Digit Span | Verbal working memory, auditory attention | 3–5 min |
| Memory Matrix | Visual memory, pattern recognition, spatial recall | 4–6 min |
| Match Pairs | Processing speed, visual recognition, short-term consolidation | 3–7 min |

Implementation properties:

1. **Deterministic scoring.** Every game's scoring function is pure +
   seeded; unit tests verify identical output for fixed inputs (PS-006
   §"Verification").
2. **Bounded adaptive difficulty.** ±15 % per session over a rolling
   7-session window; no per-day swing > 30 % (PS-006 §"Risks").
3. **Cognitive Profile clearly labelled.** Five-dimension vector is a
   simplification — every UI surface that exposes the profile carries
   "for self-tracking, not diagnostic" copy.
4. **My Journey is the daily anchor.** 10 chapters × 20–30 steps;
   adaptive engine selects 3 games per day (strength + weakness + random)
   per PRD §3.1.3 daily-workout flow.

## 2. Architecture

```
apps/web/src/modules/brain-training/
  ├─ TrainRoute.tsx                   (was PhaseStub)
  ├─ Home.tsx                         /train — Today's Workout + library + radar
  ├─ GameRunner.tsx                   /train/game/:gameId
  ├─ Journey.tsx                      /train/journey
  └─ games/
       ├─ stroop/
       │   ├─ StroopGame.tsx
       │   └─ stroop.scoring.ts        deterministic scorer
       ├─ corsi/
       │   ├─ CorsiBlocks.tsx
       │   └─ corsi.scoring.ts
       ├─ digit-span/
       │   ├─ DigitSpan.tsx
       │   └─ digit-span.scoring.ts
       ├─ memory-matrix/
       │   ├─ MemoryMatrix.tsx
       │   └─ memory-matrix.scoring.ts
       └─ match-pairs/
           ├─ MatchPairs.tsx
           └─ match-pairs.scoring.ts

packages/@njz-os/analytics/src/
  ├─ profile.ts                       (existing) CognitiveProfile + helpers
  ├─ workout.ts                       (existing) WorkoutPlan + suggestion
  ├─ adaptive.ts                      Difficulty adjustment (ADR-0018)
  ├─ scoring.ts                       Cross-game CognitiveProfile update
  ├─ percentile.ts                    Cohort percentile via age band
  └─ journey.ts                       My Journey chapter/step state

content/journey/                      My Journey chapters as JSON
  ├─ ch01-attention-foundations.json
  ├─ ch02-working-memory.json
  └─ ... (10 chapters)
```

Trade-offs already decided (PS-006):

- Five games at Phase-2 launch (not three, not seven) — matches
  competitor floor (Impulse) and allows full Cognitive Profile coverage.
- Cognitive Profile is a 5-dimension vector (memory, attention, speed,
  flexibility, spatial) — already typed in `@njz-os/analytics/src/profile.ts`.
- Three skill trees (Memory / Attention / Speed) cross-cut the games.
- "For self-tracking, not diagnostic" framing is non-negotiable
  (PS-006 §"Risks"); never approach clinical claims.

Architecture extensions for impl:

- **Per-game Canvas/SVG choice.** Stroop, Digit Span, Match Pairs are
  DOM-friendly (text + cards). Corsi Blocks and Memory Matrix are
  Canvas-friendly (grid + timing precision). Both stacks coexist; no
  single rendering decision.
- **Audio for Digit Span.** Uses Lane B's audio engine for TTS-played
  digit sequences via the browser's `SpeechSynthesis` API; falls back
  to on-screen digit display under reduced-motion / SpeechSynthesis
  unsupported.
- **Journey chapter content as code.** `content/journey/*.json` ship
  in repo; build-time validator ensures every step's prerequisites
  reference real games + score thresholds.
- **Adaptive engine is pure.** `applyAdaptive(prev, session)` is a
  pure function over the user's session history. Unit-tested against
  oscillation cases per PS-006 §"Verification".

## 3. Domain types & contracts

### Existing types (`@njz-os/analytics/src/profile.ts`, `workout.ts`)

`CognitiveProfile` (5-dim vector), `CognitiveDomain`, `Percentile`,
`WorkoutPlan`, `WorkoutSlot`, `GameId`, `weakestDomain`, `emptyProfile`,
`scoreSession`, `suggestWorkout` declared at Phase-0 stubs. Lane B'
implements behaviour + extends.

```ts
// packages/@njz-os/analytics/src/profile.ts (extend)
export interface CognitiveProfileWithMeta {
  vector: CognitiveProfile;
  updatedAt: string;
  sessionCount: number;        // total games played
  lastSessionAt?: string;
}

// packages/@njz-os/analytics/src/scoring.ts (new)
export interface GameSession {
  gameId: GameId;
  startedAt: string;
  endedAt: string;
  score: number;
  difficulty: number;          // 0..100 normalised
  rawMetrics: Record<string, number>; // per-game (Corsi span, Stroop accuracy, etc.)
}

export function scoreSession(profile: CognitiveProfileWithMeta, session: GameSession): CognitiveProfileWithMeta;
export function buildWorkout(profile: CognitiveProfileWithMeta, mode: 'morning' | 'evening' | 'random'): WorkoutPlan;
```

### Adaptive engine surface (`adaptive.ts`)

```ts
// packages/@njz-os/analytics/src/adaptive.ts (new)
export interface AdaptiveState {
  gameId: GameId;
  difficulty: number;          // 0..100; default 50 for first session
  rollingWindow: number[];     // last 7 session scores (normalised 0..1)
  perDaySwing: number;         // accumulated |Δdifficulty| today
}

export function applyAdaptive(prev: AdaptiveState, session: GameSession): AdaptiveState;

// Rules:
//   accuracy = session.score / session.maxScore  (normalised 0..1)
//   targetAccuracy = 0.7
//   delta = (accuracy - targetAccuracy) * 30      (so ±0.5 → ±15)
//   delta = clamp(delta, -15, +15)
//   if (prev.perDaySwing + |delta|) > 30: cap to leave room within 30
//   newDifficulty = clamp(prev.difficulty + delta, 0, 100)
//   rollingWindow shifts; perDaySwing resets at UTC midnight
```

Anti-oscillation: rolling-window check ensures delta doesn't whipsaw.

### Per-game scoring contract

Every game ships `<game>.scoring.ts`:

```ts
export interface GameInput {
  difficulty: number;          // 0..100 from AdaptiveState
  seed: number;                // for deterministic test runs
}

export interface GameRound {
  // game-specific shape
}

export function generateRound(input: GameInput): GameRound;
export function scoreRound(round: GameRound, response: ...): { correct: boolean; reactionMs: number };
export function aggregate(rounds: ScoredRound[]): GameSession;
```

Determinism: `(difficulty, seed)` always produces identical `GameRound`.
Tests verify with fixed seeds.

### My Journey

```ts
// packages/@njz-os/analytics/src/journey.ts (new)
export interface JourneyChapter {
  id: string;
  index: number;
  title: string;
  description: string;
  skillBranch: 'memory' | 'attention' | 'speed';
  steps: JourneyStep[];
  unlockRequirements: ChapterUnlock;
}

export interface JourneyStep {
  id: string;
  description: string;
  gameId: GameId;
  objective: { kind: 'min_score' | 'min_streak' | 'span_threshold'; value: number };
  completed?: boolean;
  completedAt?: string;
}

export interface ChapterUnlock {
  requiredChapterIds: string[];     // prerequisite chapters
  requiredCognitiveScore?: { domain: CognitiveDomain; min: number };
}

export interface UserJourneyState {
  userId: UserId;
  completedSteps: string[];         // step IDs
  completedChapters: string[];      // chapter IDs
  currentChapterId: string;
}
```

### Vaultbrain endpoints

| Method | Path | When |
|--------|------|------|
| GET | `/users/{u}/cognitive-profile` | Home radar mount |
| GET | `/users/{u}/brain/sessions?since=` | recent history for adaptive engine |
| POST | `/users/{u}/brain/sessions` | session complete; persists profile update + journey progress |
| GET | `/users/{u}/journey` | Journey route hydration |
| GET | `/users/{u}/brain/today-workout` | Today's Workout for Home view |

### Content catalog

`content/journey/<chapter>.json` parsed at build time by
`tools/content/build-journey.mjs` → `apps/web/public/journey/INDEX.json`.
Validator: every step's `gameId` exists; every `requiredChapterId`
references a defined chapter; no cycles.

## 4. Implementation walkthrough — task by task

### Task B'1 — Adaptive engine (open ADR-0018 first)

`packages/@njz-os/analytics/src/adaptive.ts`. Open ADR-0018 documenting
the ±15 % bound, 30 %-per-day cap, and rolling-7-session window. Land
the ADR before the code.

Unit tests verify:
- Two consecutive perfect sessions raise difficulty by max +15.
- Two consecutive bottom-out sessions drop difficulty by max -15.
- 5 alternating sessions don't oscillate beyond ±30.
- Per-day cap resets at UTC midnight.

Commit (post-ADR-0018): `feat(analytics): adaptive-difficulty engine`.

### Task B'2 — Stroop Test (first game; template for the rest)

`apps/web/src/modules/brain-training/games/stroop/`. Color words in
conflicting ink colors; user identifies ink color, not word.

Difficulty mapping (PRD §3.1.2):
- Level 1 (difficulty 0): 2 colors, 2 s per item
- Level 50 (difficulty 100): 6 colors, 0.8 s per item

Pure scoring functions in `stroop.scoring.ts`. Vitest covers
generate → score round trip.

Commit: `feat(brain/stroop): Stroop Test game + deterministic scoring`.

### Task B'3 — Corsi Blocks

`apps/web/src/modules/brain-training/games/corsi/`. Grid of blocks
light up in sequence; user reproduces. Forward span (standard) +
Reverse span (unlocked at user level 10).

Canvas-rendered grid (3×3 to 6×6 based on difficulty). Animation
timing tuned per ADR (could surface a follow-up ADR if timing-precision
issues arise).

Commit: `feat(brain/corsi): Corsi Blocks game + span tracking`.

### Task B'4 — Digit Span

`apps/web/src/modules/brain-training/games/digit-span/`. Spoken
digits via `SpeechSynthesis` API. Forward + Backward + Dual span.

Fallback: on `SpeechSynthesis` unsupported, show digits on-screen one
at a time. Document the degradation.

Commit: `feat(brain/digit-span): Digit Span game with TTS + fallback`.

### Task B'5 — Memory Matrix

`apps/web/src/modules/brain-training/games/memory-matrix/`. Grid of
lit cells flashes; user reproduces. Classic + Obstacle (red traps) +
Timed Blitz variants.

Canvas-rendered grid (3×3 to 6×6). Flash duration scales with
difficulty.

Commit: `feat(brain/memory-matrix): Memory Matrix game + 3 modes`.

### Task B'6 — Match Pairs

`apps/web/src/modules/brain-training/games/match-pairs/`. Card-
matching with Classic + Moving + Timed Blitz variants. Deck size
6 pairs (Level 1) to 20 pairs (Level 50).

Card themes unlock matching PolyCo.World furniture themes (PRD §3.1.2
Game 5).

Commit: `feat(brain/match-pairs): Match Pairs game + theme variants`.

### Task B'7 — Cognitive Profile + scoring

Implement `scoring.ts`'s `scoreSession()` that updates the profile
vector. Per PS-006 §3.1.4, the profile is exposed via:

- Cognitive Profile (5-dim radar) — free
- Daily Score (today's totals) — free
- Streak Tracker — free
- Percentile Ranking — free
- Historical Trends (30/60/90 day) — premium
- Detailed Breakdown — premium
- Cognitive Age estimate — premium
- Export CSV/JSON — premium

`Home.tsx` shows the 5-dim radar via D3 or Recharts.

Commit: `feat(brain): Cognitive Profile + radar + tier gating`.

### Task B'8 — My Journey

`Journey.tsx` mounts the chapter view. Each chapter has 20–30 steps
with specific objectives. Build seed chapters: Chapter 1 "Attention
Foundations" (Stroop-heavy), Chapter 2 "Working Memory" (Digit Span +
Corsi), Chapter 3 "Visual Recognition" (Memory Matrix + Match Pairs).
Chapters 4–10 in Phase-3 expansion.

Daily Workout flow per PRD §3.1.3 — 3-game plan (strength + weakness
+ random); 10–15 min total.

Commit: `feat(brain): My Journey chapter view + Today's Workout`.

### Task B'9 — Module home + integrations

`Home.tsx`: Today's Workout card, game library grid, profile radar,
streak tracker, percentile.

Integration with PolyCo.World per PS-006: workout completion produces
"Neural Dust" (decorative currency event); chapter completion adds a
wing to the Dojo. Both via canonical event taxonomy in Lane F.

Integration with Focus Hero: completing a brain training game while
not in a focus session is its own ProgressionEvent; during a focus
session, it also counts toward that session's productivity.

Commit: `feat(web/brain): module home with workout, library, radar, streak`.

### Task B'10 — Tests + a11y + gate flip

Unit tests on each game's scorer (deterministic with fixed seed);
adaptive engine oscillation tests; profile-update tests against
canned session sequences. E2E: complete a Today's Workout (3 games),
verify XP grant + profile vector update. A11y: keyboard-only play of
each game where possible (Stroop yes; Match Pairs yes; Corsi/Matrix
need creative keyboard mapping).

A8-style gate flip reserved for orchestrator.

Commit: `test(brain): unit (per-game scoring + adaptive + profile) + E2E`.

## 5. Telemetry & analytics events

| Event `kind` | When | Payload |
|--------------|------|---------|
| `brain.session.start` | game enters first round | `{ userId, gameId, difficulty, mode }` |
| `brain.session.complete` | last round scored | `{ userId, gameId, difficulty, score, durationMs, rawMetrics }` |
| `brain.session.abandon` | user exits mid-game | `{ userId, gameId, roundsCompleted }` |
| `brain.workout.start` | Today's Workout opens first game | `{ userId, plan: [gameId, gameId, gameId] }` |
| `brain.workout.complete` | last of 3 games done | `{ userId, durationMs, profileDelta }` |
| `brain.journey.step.complete` | step objective met | `{ userId, chapterId, stepId }` |
| `brain.journey.chapter.complete` | last step of chapter | `{ userId, chapterId }` |
| `brain.profile.percentile-band-change` | user crosses a percentile band threshold | `{ userId, domain, from, to }` |
| `brain.personal-best` | new high score on a game | `{ userId, gameId, score }` |

Extends `contracts/events/progression-events.json` via Lane F.

OKR mapping:

- **PRD §2.3.2 Month-6 target** — "Brain Training 40 % of DAU, 12 min
  avg session, 30 % 7-day streak"; `brain.workout.start` and
  `.complete` cover both DAU% and session-length; consecutive days
  drive streak.
- **MARKET_REVIEW.md 6–9 % conversion premium** — premium-tier metrics
  (Historical Trends, Cognitive Age) are the upsell hooks; track via
  `tier.upgrade` event correlated with `brain.workout.complete` cohort.
- **PRD §3.1 brain-training-helps-attention 69.3 % statistic** — survey
  the cohort at M3 to validate; not a code event, but the survey
  cohort is `brain.session.complete` users.

## 6. Test plan

| Tier | Tooling | Target |
|------|---------|--------|
| Unit | Vitest | Each game's `generateRound(seed, difficulty)` is deterministic; identical seed → identical round |
| Unit | Vitest | Each game's `scoreRound` correctly computes score + reaction time from response |
| Unit | Vitest | Adaptive engine: ±15 % bound per session; ±30 % per day cap; no 5-session oscillation > 30 % |
| Unit | Vitest | `scoreSession` updates only the game's domain; cross-domain leakage zero |
| Unit | Vitest | Percentile cohort lookup: age 25 user with profile.memory = 60 returns expected percentile |
| Integration | Vitest + msw | Vaultbrain sync: session.complete → profile + journey both update atomically |
| E2E | Playwright | Complete Today's Workout (3 games via fixed seed); verify XP + profile delta |
| E2E | Playwright | Replay a personal-best session; verify `brain.personal-best` fires only once per gameId |
| Mobile | manual iPhone 12 + mid-range Android | All 5 games playable; Corsi grid touch targets ≥ 44 px |
| a11y | axe + manual | Stroop / Digit Span / Match Pairs keyboard-playable; Corsi / Memory Matrix offer keyboard mapping |
| a11y | manual screen reader | Cognitive Profile radar exposes per-domain values as a `<table>` |
| Perf | Lighthouse | ≥ 85 on `/train`; ≥ 90 on `/train/game/:gameId` |
| Validity | content review | Each game's domain claim verified against published neuropsychology references (CogniFit Corsi standard, etc.) |

## 7. Accessibility plan (WCAG 2.2 AA)

| Component | Requirement |
|-----------|-------------|
| `Home` radar chart | Provide an equivalent `<table>` of per-domain scores; `aria-describedby` links chart to table |
| `GameRunner` | Pause/quit always reachable via Esc; current round announced via `aria-live="polite"` |
| Stroop UI | Color names labelled; users with color blindness offered a "high-contrast palette" mode |
| Corsi Blocks | Keyboard map: numpad 1-9 maps to grid cells; arrows + Enter alternative |
| Digit Span | TTS announces digits; on-screen fallback for unsupported browsers; text input always works |
| Memory Matrix | Keyboard map for cells; flash duration adjustable for cognitive-disability users |
| Match Pairs | Tab to navigate cards; Space/Enter to flip |
| `Journey` chapter view | Step list as ordered list with completion state; current step has `aria-current="step"` |
| Reduced motion | Disable animation transitions between rounds; cells flash but don't fly |
| Color contrast | All game UIs pass 4.5:1; Stroop colors selected from a contrast-validated palette |
| Self-tracking-not-diagnostic copy | Visible on every screen exposing the Cognitive Profile or Cognitive Age |

## 8. Risk register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Cognitive Profile misinterpreted as diagnostic | H | H | "For self-tracking, not diagnostic" copy mandatory on every profile UI; legal-friendly framing |
| Game design quality variance across 5 games | M | H | Per-game designer review; user-test cohort at M3 before broader rollout |
| Adaptive engine oscillates → user frustration | M | M | ADR-0018 bounds; unit tests for non-oscillation; dampening if needed |
| Percentile cohort baseline thin at launch (no real users yet) | H | M | Bootstrap with public neuropsychology references; refine with first-1000-user cohort (ADR-0019 candidate) |
| SpeechSynthesis voice quality varies; Digit Span feels janky | M | L | On-screen fallback always available |
| Animation perf on low-end Android → laggy Memory Matrix | M | M | Canvas + requestAnimationFrame; tier-detect to slower flash on low-end |
| User cheats by replaying same seed | L | L | Server-side: seed rotation per session; client can't request a fixed seed in production |
| Game content gets stale after first 30 days | M | M | Phase 3 expansion of games + variants; My Journey provides progression even with fixed game count |
| Children play; we have no COPPA story | M | M | Phase-1 PRD already targets 13+ (PERSONAS Tertiary tier); enforce age-gate at signup (Lane E) |
| Streak abuse via background autoplay scripts | L | M | Session.complete requires user-input events (keyboard/pointer) within the past 30 s; server checks |

## 9. Cross-lane handoffs

| Direction | What | Counterparty |
|-----------|------|--------------|
| **Consumes** auth + tier | `useAuth().userId`, `useTier()` for premium-gated metrics | Lane E |
| **Consumes** soundscape engine | optional brain-training warm-up before a "Focus Now" session per PS-006 "Soundscapes integration" | Lane B `@njz-os/audio-engine` |
| **Consumes** FocusSession state | brain-training XP boosts hero progression rate; counts inside focus sessions | Lane A `useFocusSession()` |
| **Emits** `brain.session.complete` (Neural Dust) | PolyCo.World decoration unlock | Lane C subscriber |
| **Emits** `brain.journey.chapter.complete` | PolyCo Office Dojo gets a new wing | Lane C subscriber + asset (Phase 3 polish) |
| **Shares** "Memory Tomes" with Micro-Learning | High Digit Span / Memory Matrix scores unlock collectible books that appear in Office Library alongside Lane L's completed-deck spines | Lane L (Micro-Learning) → Lane C decoration-rules |
| **Coordinates** new `brain.*` events | canonical taxonomy | Lane F |

## 10. Out of scope (this module / phase)

- Cross-user leaderboards — Phase 3 (PS-006 §"Out of scope").
- Games 6+ — Phase 3+ expansion.
- Clinical-grade assessment positioning — **never** (educational only).
- Wearable input (heart rate, EEG) — speculative, Phase 5+.
- Adaptive engine ML model — Phase 4 via agent-gateway; Phase 2 ships
  the simple bounded ±15 % engine.
- Cohort-comparison leaderboards (anonymous percentile cohorts are OK;
  named comparison is Phase 3).
- COPPA-compliant under-13 mode — Phase 5+; Phase 2 enforces 13+ at
  signup (Lane E age-gate).
- Therapy-adjacent claims of any kind — never.

## 11. Open questions / TODOs for implementation

| Question | Options | Recommended default | Decision owner |
|----------|---------|---------------------|-----------------|
| **Adaptive engine bounds** (PRIMARY) | (a) ±15 % per session, ±30 % per day (PS-006) (b) wider bands | (a) — well-tested in similar products; tighter is safer than wider | Architect → ADR-0018 |
| **Cognitive-profile baseline cohort** | (a) public neuropsychology references (Lumosity, CogniFit) (b) wait for first-1000 internal cohort (c) hybrid: (a) until N=1000, then transition | (c) — bootstrap with (a); transition rule documented | Architect → ADR-0019 |
| Game UI stack | (a) Canvas everywhere (b) DOM for text-heavy, Canvas for grid (c) WebGL | (b) — performance where needed, simpler where DOM suffices | Implementer |
| Digit Span audio source | (a) SpeechSynthesis (b) pre-recorded audio | (a) — no asset bandwidth cost; fall back to on-screen | Implementer |
| Where does Cognitive Age formula live? | (a) `packages/@njz-os/analytics/src/cognitive-age.ts` (b) `services/api` Postgres function | (a) — pure client function; predictable | Implementer |
| Should premium-only profile features be visually hidden or shown with upgrade-prompt? | (a) hidden (b) shown with lock + upgrade CTA | (b) — discovery hook for free → premium conversion | Designer |
| Journey chapter content authoring — repo or CMS? | (a) repo `content/journey/*.json` (b) CMS | (a) — Phase 2; (b) Phase 4+ if authors grow | Coordinator |
| First-time-play onboarding per game | (a) inline tutorial (b) external help docs (c) skip-able mini-demo | (c) — skip-able mini-demo; tracks `brain.tutorial.complete` to suppress next time | Designer |
| Color-blind safe palette for Stroop | (a) detect via `prefers-color-scheme` (b) settings toggle | (b) — explicit user choice; default to high-contrast safe palette | Designer |
| Match Pairs card themes — how many? | (a) 1 default + premium unlocks (b) 5 free + 10 premium | (a) Phase 2; (b) Phase 3 once Lane C asset pipeline ships theme assets | Designer |
| Should under-performance trigger encouragement nudges? | (a) yes (rare, opt-out) (b) no | (b) — ROOT_AXIOMS PR-03 says no nagging; respect user agency | Architect |
| Seeded vs random in production | (a) random per session (b) seeded by session-id | (a) — production sessions are randomly seeded; tests pin via internal API | Implementer |
| Reverse-span unlock at level 10 — game-specific level or My-Journey-mediated? | (a) per-game level (PS-006) (b) journey-mediated | (a) — matches PS-006 PRD §3.1.2 directly | Architect |

---

> **When implementing**, open ADR-0018 first (adaptive engine bounds)
> and ADR-0019 second (cognitive profile baseline). Both inform the
> Phase 2 launch decisions. Per ROOT_AXIOMS/03_PROCEDURES/00-add-an-adr,
> ADRs land before any code that depends on them.

> **Do NOT** touch `.agents/PHASE_GATES.md`, ADRs 0001–0014, or other
> module routes. Stay inside `apps/web/src/modules/brain-training/`,
> `packages/@njz-os/analytics/`, `content/journey/`, and
> `tools/content/build-journey.mjs`.

> **See also:** PS-006, PRD §3.1, MARKET_REVIEW.md (Lumosity / CogniFit /
> Impulse references, 6–9 % conversion premium), PERSONAS.md (Primary tier
> morning cognitive warm-up; Tertiary competitive scores), Lane C asset
> pipeline (for content build-time validator pattern), Lane L Micro-
> Learning (Memory Tomes shared unlock).

## 12. Enterprise refinement plan

This lane's implementation has an enterprise-grade refinement plan
documented at `docs/program-management/PR-25-portfolio-uplift.md`. The
B′-lane work items referenced there are:

- **PRX-25-PERF-03** — Animation-frame budget audit (per-game tick
  budgets, dev overlay, regression test).
- **PRX-25-PATCH-03** — Cross-lane error boundary (graceful game
  crash recovery without losing the My Journey daily state).
- **PRX-25-ENH-04** — Pre-computed cohort percentiles for the
  Cognitive Profile header band (Phase-2 launch screen).

In addition, the lane consumes **PRX-25-EPIC-01** (`vaultbrain-client`)
for game-result records + cognitive-profile reads,
**PRX-25-PATCH-02** (progression hook) for the My-Journey daily streak,
and **PRX-25-ENH-05** (design-token compile step) for the games'
shared palette + motion contract. Open PR-25 before starting Task
B′1 to confirm the per-game baseline cohort sequencing.
