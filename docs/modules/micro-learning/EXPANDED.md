[Ver001.000]

# Micro-Learning — Expanded Module Documentation

> **Phase-2 L** in the Stage 3 documentation sprint continuation.
> Implementation-ready spec for the next agent picking up Micro-Learning.

## 1. Module identity & scope

| Field | Value |
|-------|-------|
| **Module name** | Micro-Learning |
| **Slug (code)** | `micro-learning` |
| **Status** | Documented (Accepted); implementation pending Phase 2 |
| **Owner role** | Implementer (with Designer for card aesthetic + Content/Legal for licensing) |
| **Channel** | `packages-engines` + `web-app` |
| **Gate protected** | `G2.micro-learning` (currently LOCKED) |
| **Phase** | 2 (Phase-1 exit gates this); Phase 4+ expands content catalogue past 500 cards |
| **Source ADRs** | **None Phase-1**. Recommends new ADR-0016 (content licensing model — original + CC-licensed; legal review) and ADR-0017 (asset hosting for card illustrations — vaultbrain blob in Phase 2, Cloudflare R2 + KV catalog in Phase 4+). See §11 |
| **Source PS** | `docs/prototype-systems/PS-005-micro-learning.md` |
| **Parent docs** | PRD §3.5 (Micro-Learning), MARKET_REVIEW.md (Imprint reference + $3.01–5.06 B segment), PERSONAS.md (Curious Learner tertiary tier, Primary tier daily-habit reinforcement) |
| **Plan reference** | Stage 3 continuation per `.agents/handoff/stage-3-doc-expansion-next-session.md` |

Micro-Learning is the **bite-sized retention engine**. Bite-sized visual
card lessons in the Imprint tap-forward format. Three structural roles
across the persona stack:

- **Curious Learner (Tertiary):** primary acquisition surface — free
  cards drive social shares and viral growth.
- **Balanced Achiever (Primary):** daily-habit reinforcement during
  commutes, coffee breaks, queueing.
- **Creative Professional (Secondary):** focused topic deep dives in
  spaced-repetition format.

Implementation properties:

1. **Tap-forward visual cards.** Full-bleed illustration + 3–7 word
   headline + 1–2 sentence insight + expandable detail. Card structure
   per PRD §3.5.2.
2. **Spaced-repetition built in.** SM-2 algorithm schedules reviews
   based on user quality ratings; review queue at `/learn/review`.
3. **Connection-card graph.** Every card carries optional links to
   related concepts. Reading a card surfaces 1–3 connections; following
   one navigates without losing position (back-stack preserved).
4. **Content-pipeline discipline.** Original + CC-attributed only at
   Phase 2; community contributions defer to Phase 3 with editorial
   gate. Legal review pre-launch.

## 2. Architecture

```
apps/web/src/modules/micro-learning/
  ├─ LearnRoute.tsx                   (was PhaseStub)
  ├─ Home.tsx                         /learn — deck library + recs
  ├─ DeckReader.tsx                   /learn/d/:deck — tap-forward
  ├─ Review.tsx                       /learn/review — SM-2 queue
  ├─ Card.tsx                         single card view (used by both)
  └─ components/
       ├─ DeckCard.tsx
       ├─ CardArtwork.tsx              full-bleed illustration
       ├─ ConnectionPills.tsx          related-concept chips
       ├─ BookmarkButton.tsx
       ├─ QualityRater.tsx             ease/quality 0-5 input for SM-2
       └─ DetailExpander.tsx           "Tell me more" toggle

packages/@njz-os/learning-cards/src/
  ├─ card.ts                          (existing) types
  ├─ deck.ts                          (existing) types
  ├─ spaced-repetition.ts             (existing) types
  ├─ sm2.ts                           SM-2 algorithm (deterministic)
  ├─ connections.ts                   Connection-graph traversal
  ├─ persistence.ts                   Vaultbrain bookmark + schedule sync
  └─ recommend.ts                     Next-deck recommender (Phase 2 simple; Phase 4 ML)

content/cards/                        Card content as MDX + JSON metadata
  ├─ <deck-id>/
  │   ├─ deck.json                    Deck metadata
  │   └─ cards/
  │       ├─ <card-id>.mdx
  │       └─ <card-id>.illustration.png
  └─ INDEX.json                       Build-time-generated catalog
```

Trade-offs already decided (PS-005):

- Imprint-style tap-forward interaction model (PRD §3.5.2).
- Three content types: Quick Read (5–10 cards, 2–3 min), Series (multi-
  day), Deep Dive (15–25 cards). Quick Read ships Phase 2; Series and
  Deep Dive in Phase 3.
- SM-2 algorithm for spaced repetition (PS-005 §"Verification" mentions
  "canonical quality inputs"; SM-2 is the canonical name).
- 50+ cards at Phase-2 launch; 500+ by Phase 4 with community
  contribution.

Architecture extensions for impl:

- **Content as code.** Card MDX + JSON ship in `content/cards/`
  directory; build-time pipeline emits a single `INDEX.json` catalog
  consumed by the runtime. New cards = repo PR (Phase 2). Community
  authoring (Phase 3) layers on top via a separate editorial CMS.
- **Illustration hosting.** Phase 2: PNG/SVG in repo `content/cards/`,
  served from `apps/web/public/cards/`. Phase 4: migrate to
  R2 + KV catalog (per ADR-0017 recommendation). Same surface.
- **Offline reading.** Service worker caches the user's downloaded decks
  for offline reading on commutes (PS-005 §"Purpose"). Phase 2 caches
  on-demand; Phase 3 explicit "Download deck" button.

## 3. Domain types & contracts

### Existing types (`@njz-os/learning-cards/src/card.ts`, `deck.ts`, `spaced-repetition.ts`)

`Card`, `Deck`, `DeckKind`, `ReviewSchedule`, `Quality` are defined at
Phase-0 stubs. Lane L extends and concretises.

```ts
// packages/@njz-os/learning-cards/src/card.ts (extend)
export interface Card {
  id: string;
  illustration: string;        // url path
  headline: string;            // 3-7 words, Space Grotesk bold
  insight: string;             // 1-2 sentences, Inter body
  detail?: string;             // expandable "Tell me more"
  tags: string[];
  connections: string[];       // card IDs of related concepts
  source?: CardAttribution;    // for CC-licensed content
}

export interface CardAttribution {
  author?: string;
  title?: string;
  publisher?: string;
  url?: string;
  license: 'original' | 'CC0' | 'CC-BY-4.0' | 'CC-BY-SA-4.0' | 'public-domain';
}

// packages/@njz-os/learning-cards/src/deck.ts (extend)
export type DeckKind = 'quick-read' | 'series' | 'deep-dive';

export interface Deck {
  id: string;
  title: string;
  description: string;
  kind: DeckKind;
  cards: Card[];
  estimatedMinutes: number;
  tags: string[];
  thumbnailUrl?: string;
  publishedAt: string;
  isPremium: boolean;
}
```

### SM-2 algorithm surface (`sm2.ts`)

```ts
// packages/@njz-os/learning-cards/src/sm2.ts (new)
export type Quality = 0 | 1 | 2 | 3 | 4 | 5; // 0 worst, 5 perfect

export function applyReview(prev: ReviewSchedule, q: Quality, now = new Date()): ReviewSchedule {
  // Canonical SM-2:
  //   if q < 3: repetitions = 0; interval = 1 day
  //   else:     repetitions += 1
  //             interval = if reps == 1 then 1
  //                        elif reps == 2 then 6
  //                        else round(prev.interval * easeFactor)
  //   easeFactor = max(1.3, easeFactor + (0.1 - (5-q) * (0.08 + (5-q) * 0.02)))
  // Returns new ReviewSchedule with nextReviewAt = now + interval days.
}

export function newSchedule(cardId: string): ReviewSchedule;
```

Determinism: same `(prev, q)` always produces the same next schedule.
Verified by unit tests with canonical quality inputs.

### Connection graph (`connections.ts`)

```ts
// packages/@njz-os/learning-cards/src/connections.ts (new)
export interface ConnectionGraph {
  getConnections(cardId: string): Card[];     // direct neighbours
  getPath(from: string, to: string): Card[];  // BFS shortest path
  getSurprise(cardId: string, seenIds: Set<string>): Card | null;
                                              // unseen neighbour
}

export function createGraph(allCards: Card[]): ConnectionGraph;
```

### Recommender (`recommend.ts`)

```ts
export interface DeckRecommender {
  next(userId: UserId, opts?: { limit?: number }): Promise<Deck[]>;
}

export function createRecommender(opts: {
  catalog: Deck[];                   // all decks from INDEX.json
  history: () => Promise<UserHistory>; // user's reads + bookmarks via vaultbrain
}): DeckRecommender;
```

Phase 2: simple — recommend decks whose tags overlap with user's
recent reads but haven't been read. Phase 4: ML-driven via
agent-gateway integration.

### Vaultbrain endpoints

| Method | Path | When |
|--------|------|------|
| GET | `/users/{u}/learning/bookmarks` | Home + Review hydration |
| POST | `/users/{u}/learning/bookmarks` | toggle bookmark on card |
| GET | `/users/{u}/learning/schedule` | Review-queue hydration |
| POST | `/users/{u}/learning/review` | apply SM-2 review (q rating) |
| GET | `/users/{u}/learning/history` | recommender input |
| POST | `/users/{u}/learning/deck/complete` | deck completion event |

### Content catalog

Build-time script `tools/content/build-cards.mjs` walks
`content/cards/<deck-id>/cards/*.mdx`, parses front-matter, emits
`apps/web/public/cards/INDEX.json` and copies illustrations to
`apps/web/public/cards/illustrations/`.

`pnpm content:build-cards` wired in root `package.json`. CI runs in the
asset-pipeline lane (Lane C's `pnpm assets:validate` extends to catch
orphan cards too).

## 4. Implementation walkthrough — task by task

### Task L1 — Build-time content catalog

`tools/content/build-cards.mjs` per §3 description. Validates each
card MDX (front-matter required fields: id, headline, insight,
illustration, license). Emits `INDEX.json` keyed by card-id.

Authors a seed catalog: 1 Quick-Read deck of 7 cards on "The Feynman
Technique" (PRD §3.5.2 example), all original content. Illustrations
hand-drawn or CC0.

Commit: `feat(content): card build-time catalog + Feynman seed deck`.

### Task L2 — SM-2 algorithm

`packages/@njz-os/learning-cards/src/sm2.ts`. Unit-test against
canonical quality sequences from the SM-2 reference paper
(SuperMemo 2). Property: `prev → applyReview(prev, 5) → applyReview(p2, 5) → ...`
produces the canonical interval growth.

Commit: `feat(learning): SM-2 spaced-repetition algorithm`.

### Task L3 — Connection graph

`connections.ts` per §3. BFS over the `Card.connections[]` adjacency.
Unit tests: graph round-trip, cycle handling, surprise-card selection.

Commit: `feat(learning): card connection graph + surprise picker`.

### Task L4 — Vaultbrain persistence

`persistence.ts` wraps vaultbrain endpoints (§3 table). Local cache via
TanStack Query (10 s stale, 5 min cache). Offline queue for review
applications.

Commit: `feat(learning): vaultbrain persistence (bookmarks, schedule, history)`.

### Task L5 — Deck reader UI

`DeckReader.tsx` at `/learn/d/:deck`. Tap-forward interaction (right
edge → next, left edge → previous, swipe gestures, double-tap
bookmark, long-press share). Connection pills under the insight.
Detail expander.

Commit: `feat(web/learn): deck reader with tap-forward interaction`.

### Task L6 — Module home + recommender

`Home.tsx` at `/learn`. Deck library grid with thumbnails + estimated
minutes + tags. "Recommended for you" rail (top 3 from recommender).
"Bookmarked" section. Search/filter by tag.

Commit: `feat(web/learn): module home with deck library + recommendations`.

### Task L7 — Review queue

`Review.tsx` at `/learn/review`. Daily review queue surfaced from
SM-2 schedule. Card view + quality rater (0–5 buttons). On rate,
applies SM-2, persists via vaultbrain.

Commit: `feat(web/learn): SM-2 review queue with quality rater`.

### Task L8 — Tests + a11y + gate flip

Unit (SM-2 determinism, connection BFS, recommender filter), E2E
(complete a 7-card deck on mobile; verify completion event), a11y
(card reader keyboard-navigable, connections labelled).

A8-style gate flip reserved for orchestrator.

Commit: `test(learning): unit + E2E + a11y baseline`.

## 5. Telemetry & analytics events

| Event `kind` | When | Payload |
|--------------|------|---------|
| `learning.card.open` | card mounted in reader | `{ userId, cardId, deckId, fromConnection?: string }` |
| `learning.card.bookmark` | bookmark toggled | `{ userId, cardId, added: boolean }` |
| `learning.card.share` | share gesture | `{ userId, cardId, target }` |
| `learning.deck.start` | first card opened in deck | `{ userId, deckId, kind }` |
| `learning.deck.complete` | last card seen | `{ userId, deckId, durationMs, cardsSeen }` |
| `learning.review.apply` | SM-2 quality rating saved | `{ userId, cardId, quality, nextReviewAt }` |
| `learning.connection.followed` | tap on a connection pill | `{ userId, fromCardId, toCardId }` |

Extends `contracts/events/progression-events.json` — Lane F coordinates.

OKR mapping:

- **PRD §2.3.2 Month-6 target** — "Micro-Learning 30% of DAU, 10 min
  avg session, 28% 7-day streak" — `learning.deck.start` (DAU%),
  `learning.deck.complete` durations (session length),
  `learning.review.apply` consecutive days (streak).
- **O2.1 KR1** — `G2.micro-learning` flip is the Phase-2 launch box.
- **Connection-following rate** — `learning.connection.followed` /
  `learning.card.open` is an engagement-depth metric, not OKR-mapped
  in Phase 2.

## 6. Test plan

| Tier | Tooling | Target |
|------|---------|--------|
| Unit | Vitest | SM-2 produces canonical intervals for [0,5] quality sequences; round-trip preserves easeFactor |
| Unit | Vitest | Connection graph: BFS shortest path, surprise picker avoids seen cards, cycle detection |
| Unit | Vitest | Recommender filters tags correctly, never recommends a read deck |
| Integration | Vitest + msw | vaultbrain persistence layer: bookmark toggle, review apply, deck completion |
| E2E | Playwright (mobile viewport) | open `/learn/d/feynman-technique`; tap through 7 cards; verify `learning.deck.complete` fires |
| E2E | Playwright | bookmark a card; navigate away; return; bookmark persists |
| E2E | Playwright | follow a connection; back gesture returns to prior card with scroll position preserved |
| Mobile | manual iPhone 12 + mid-range Android | 5-card deck renders without layout shift; tap-forward responsive; illustrations crisp |
| a11y | axe + manual | each card reader navigable via keyboard arrows; quality rater works keyboard-only; connection pills `aria-label`led |
| Perf | Lighthouse | ≥ 85 on `/learn`; ≥ 90 on `/learn/d/:deck` (illustration-heavy but per-card lazy load) |
| Content | tools/content/build-cards | every card has required fields; every connection references a real card; every illustration file exists; every license is a known value |

## 7. Accessibility plan (WCAG 2.2 AA)

| Component | Requirement |
|-----------|-------------|
| `DeckReader` | Arrow-Left/Right also navigates; "Card X of Y" announced via `aria-live`; full card text exposed to screen reader regardless of expander state |
| `CardArtwork` | `alt` text required in every card MDX; meaningful description, not "image of X" |
| `ConnectionPills` | Each pill `<a>` with `aria-label="Related: <headline>"`; keyboard-focusable |
| `BookmarkButton` | Toggle button with `aria-pressed`; announces "Bookmarked" / "Removed bookmark" |
| `QualityRater` | Radio group with `fieldset` + `legend="How well did you remember?"`; keyboard-operable |
| `DetailExpander` | `aria-expanded` toggle; collapsed text not hidden via `display:none` (screen reader can still read on toggle) |
| Reduced motion | Disable card-slide transitions under `prefers-reduced-motion: reduce`; instant swap |
| Color contrast | Headline + insight pass 4.5:1; full-bleed illustration cannot impede readability — text on overlay scrim |
| Long-press accessibility | Share also reachable via keyboard menu (right-click / Shift-F10 on desktop; long-press is mobile-only) |

## 8. Risk register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Content licensing dispute (CC card text used without proper attribution) | M | H | Per-card `license` + `source` fields required; CI validator enforces; legal review pre-launch (recommended ADR-0016) |
| Card-quality variance feels shallow vs PS-005 §3.5 promise | M | M | Editorial gate on every card before Phase-2 merge; Connection Cards + future Deep Dive mitigate |
| Illustration bundle size grows unbounded | M | M | Per-illustration ≤ 200 KB; total ≤ 50 MB at Phase 2; CI validator enforces |
| Tap-forward feels gimmicky after novelty wears off | M | M | Spaced-repetition + Connections add depth; user analytics tracked to detect drop-off |
| Recommender shows the same decks repeatedly | M | L | Recommender penalises recently-recommended (decay over 7 days); falls back to popular if exhausted |
| SM-2 algorithm wrong (off-by-one or rounding) → user loses faith | M | H | Canonical-input unit tests; A/B against the SuperMemo reference paper outputs |
| Content authoring bottleneck — 50 cards in Phase 2 demands editorial capacity | H | M | Phase 2 ships with one seed deck (Feynman, 7 cards); expand to 50 over Months 3–4 with one weekly authoring pass |
| Mobile illustrations look bad on retina (pixelation) | M | L | 2x or vector illustrations; CI validator checks DPI |
| Bookmark conflict across devices (toggle on mobile + desktop simultaneously) | L | L | Last-write-wins acceptable; bookmarks aren't critical-path |
| User exhausts the review queue early → motivation drop | M | L | UI surfaces "Caught up! Come back tomorrow" with new-deck recommendation |

## 9. Cross-lane handoffs

| Direction | What | Counterparty |
|-----------|------|--------------|
| **Consumes** auth | `useAuth().userId` for vaultbrain persistence | Lane E |
| **Consumes** FocusSession state | completing a deck during a focus session = productive session count | Lane A `useFocusSession()` |
| **Emits** `learning.deck.complete` | PolyCo.World Office Library populates with completed-deck spine | Lane C subscriber |
| **Consumes** "Memory Tomes" from Brain Training | tomes unlocked from games (PS-006) appear in Office Library alongside completed decks | Lane B' (Brain Training) → polyworld decoration via Lane C |
| **Coordinates** new `learning.*` event names | canonical taxonomy | Lane F |
| **Consumes** UI tokens | typography + color from `@njz-os/ui` | shared |
| **Consumes** content pipeline | build-time card catalog parallels asset pipeline | Lane C's pattern, separate script |

## 10. Out of scope (this module / phase)

- User-generated decks — Phase 3 (PS-005 §"Out of scope").
- Audio narration of cards — Phase 4.
- Translated decks (i18n) — Phase 5.
- AI-generated card content — Phase 4+ via agent-gateway evaluation.
- Quiz / test mode beyond SM-2 review — Phase 4.
- Social: "X friends are reading this" — Phase 3.
- Card embedding in third-party sites (oEmbed) — Phase 4.
- Creator monetisation — Phase 5 (creator economy).
- Analytics dashboard for content authors — Phase 4.
- Push notifications for review queue — Phase 3 (native shells).

## 11. Open questions / TODOs for implementation

| Question | Options | Recommended default | Decision owner |
|----------|---------|---------------------|-----------------|
| **Content licensing model** (PRIMARY) | (a) original-only Phase 2 (b) original + CC-BY (c) original + CC + paid content | (b) — original + CC-BY with mandatory attribution; legal review | Legal + Architect → ADR-0016 |
| **Illustration hosting at scale** | (a) repo + Vercel static (b) Cloudflare R2 + KV catalog (c) Supabase storage | (a) Phase 2 (≤ 50 MB); (b) Phase 4 once catalogue grows | Architect → ADR-0017 |
| Card body format | (a) MDX (b) plain Markdown (c) JSON | (a) MDX — allows React components for interactive insets without breaking SSG | Architect |
| Tap-forward — taps or buttons? | (a) edge-tap zones only (b) explicit prev/next buttons (c) both | (c) — taps are primary mobile, buttons are accessibility fallback | Designer |
| Quality rater — 0-5 or simplified 1-4? | (a) 0-5 (canonical SM-2) (b) Again/Hard/Good/Easy (Anki-style) | (a) — canonical and well-tested; map UI labels to numbers | Architect |
| Where does the Feynman seed deck live? | (a) in repo `content/cards/feynman-technique/` (b) in vaultbrain | (a) — content-as-code for Phase 2 | Architect |
| Bookmark UX — heart or star? | (a) bookmark icon (b) heart (c) star | (a) — neutral, language-independent; matches Save semantics | Designer |
| Should incomplete reviews block opening new decks? | (a) no, always allow new (b) soft prompt | (b) soft prompt — "You have 12 cards due; review or skip?" | Designer |
| Connection-pill count — fixed or variable per card? | (a) 1-3 max (b) all available | (a) — too many is noise; surface "see more" if user wants | Designer |
| `Quality < 3` interval reset — to 1 day or shorter? | (a) 1 day (canonical SM-2) (b) immediate re-test | (a) — canonical | Architect |
| Card preloading strategy | (a) load all on deck mount (b) lazy per-card (c) prefetch next 2 | (c) — balances perceived latency with bandwidth | Implementer |
| Editorial-gate process for Phase-2 cards | (a) PR review (b) external CMS | (a) — Phase 2; (b) Phase 3 if volume warrants | Coordinator |

---

> **When implementing**, open ADR-0016 first (content licensing) and
> ADR-0017 second (illustration hosting). Both inform Task L1 (build-time
> catalog) and the per-card validator. Do not start authoring decks
> before ADR-0016 lands — licensing decisions affect what content can ship.

> **Do NOT** touch `.agents/PHASE_GATES.md`, ADRs 0001–0014, or other
> module routes. Stay inside `apps/web/src/modules/micro-learning/`,
> `packages/@njz-os/learning-cards/`, `tools/content/`, `content/cards/`,
> and `apps/web/public/cards/`.

> **See also:** PS-005, PRD §3.5, MARKET_REVIEW.md (Imprint reference),
> PERSONAS.md (Curious Learner + Primary tier daily-habit), Lane C
> asset-pipeline pattern (for build-time catalog parallels).

## 12. Enterprise refinement plan

This lane's implementation has an enterprise-grade refinement plan
documented at `docs/program-management/PR-25-portfolio-uplift.md`. The
L-lane work items referenced there are:

- **PRX-25-SPRINT-02** — SM-2 vs FSRS-5 comparative analysis (informs
  ADR-0016 / ADR-0017 sequence).
- **PRX-25-PERF-02** — Lighthouse CI integration.
- **PRX-25-PATCH-04** — Unified telemetry pipeline (per-review event batching).
- **PRX-25-PATCH-05** — Shared toast/notification surface (review feedback).
- **PRX-25-ENH-01** — IndexedDB hot-cache for vaultbrain reads
  (cards + review-history fast-path).
- **PRX-25-ENH-03** — Streaming SSR for marketing pages (the
  `/modules/micro-learning` landing).

In addition, the lane consumes **PRX-25-EPIC-01** (`vaultbrain-client`)
for card persistence, review recording, and graph queries, and
**PRX-25-PATCH-02** (progression hook) for XP-on-review display. Open
PR-25 before starting Task L1 to confirm the per-card licensing path
and the ICE-ranked sequence for this lane.
