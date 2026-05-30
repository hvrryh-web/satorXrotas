[Ver001.000]

# PR #25 — Portfolio Uplift Plan

> **Status:** Active · **Date opened:** 2026-05-30 · **PR:** hvrryh-web/satorXrotas#25
> **Branch:** `docs/stage-3-phase-2-module-expansions`
> **Author:** claude-opus-4.7 (orchestrator)
> **Audience:** the next implementation cohort working any of Phase-2 lanes
> W (Writing Space), L (Micro-Learning), or B′ (Brain Training)
>
> **Scope of this document:** enumerate the **16 enterprise-grade refinement
> items** layered on top of the 3 base EXPANDED.md docs that PR #25 ships, so
> a veteran product-development team can plan, sequence, and merge them with
> the same rigour applied to ADRs 0001–0014 and the Phase-1 lane closes.

---

## 1. Why this document exists

PR #25 ships three implementation-ready EXPANDED.md docs (Writing Space,
Micro-Learning, Brain Training). That is the *floor* — a documentation
contract a fresh subagent can implement against without further
research. This document is the **ceiling** — the refinement, sprint, and
enhancement work items that take the same three lanes from
documentation-ready to **enterprise-shippable**.

The structure (1 premium revamp + 2 sprints + 3 performance changes + 5
portfolio-integration patches + 5 functional/efficiency enhancements =
**16 items**) mirrors the enterprise rollout cadence used by mature
product organisations: one keystone uplift surrounded by smaller,
sequenced refinements that compound.

Each item below is sized for one PR / one author / one review cycle.
The IDs are stable references — DECISION_LOG entries, follow-up
handoffs, and downstream ADRs may cite them by `PRX-25-…` code.

## 2. Quality bar (acceptance for every item)

A work item closes only when **all** are demonstrably true:

- [ ] Conforms to ROOT_AXIOMS `02_STANDARDS/` (code, doc, naming, security).
- [ ] `pnpm typecheck` + `pnpm lint` + `pnpm test` + `pnpm
      doc-tier:check` all green on the PR head.
- [ ] No file touched outside the lane's declared channel (per
      `.agents/COORDINATION_PROTOCOL.md` channel list).
- [ ] Telemetry impact assessed: which `ProgressionEvent` or analytics
      event changes shape, and downstream consumer(s) updated.
- [ ] Threat-model delta documented if the change touches auth, secrets,
      vaultbrain payloads, or the calendar OAuth surface.
- [ ] Performance delta measured: Lighthouse perf score on the lane's
      primary route does not regress > 2 points vs. `main` baseline.
- [ ] One DECISION_LOG line appended on merge (date · agent · area ·
      one-sentence decision → PRX-25-…).
- [ ] One LOGBOOK note in `.agents/phase-logbooks/PHASE-1-LOGBOOK.md`
      (or PHASE-2-LOGBOOK once that file opens).

Items flagged with a 🔒 require a co-signed review (Implementer +
Security or Implementer + Critic). Items flagged with a 🧪 require a
recorded experiment design before implementation (hypothesis, metric,
ship/kill rule).

## 3. Distribution across PR #25's three lanes

| Lane | Module | Premium revamp | Sprints | Perf | Portfolio patches | Enhancements | Total |
|------|--------|----------------|---------|------|-------------------|--------------|-------|
| W | Writing Space | — | 1 | 1 | 2 | 2 | 6 |
| L | Micro-Learning | — | 1 | 1 | 2 | 2 | 6 |
| B′ | Brain Training | — | — | 1 | 1 | 1 | 3 |
| **portfolio-wide** | adapter / shared | **1** (vaultbrain-client) | — | — | — | — | 1 |
| **Total** | | **1** | **2** | **3** | **5** | **5** | **16** |

The premium revamp lands at the portfolio level (adapter layer) because
all three Phase-2 lanes consume the same `vaultbrain-client` surface,
and lifting it once benefits every downstream lane. The remaining 15
items distribute roughly proportional to each lane's expected
implementation surface (W ≈ L > B′ for Phase-2 first-wave; B′ inherits
more later from cross-lane work).

## 4. ICE scoring legend

Each item carries an **ICE score** (Impact × Confidence × Ease,
1–10 each, multiplied). Higher is better. The sequencer (orchestrator
or staff engineer) chooses the next item by descending ICE within the
lane being worked, breaking ties toward lower-risk first.

| Bucket | ICE range | Treatment |
|--------|-----------|-----------|
| Keystone | ≥ 400 | Lead architect drives; multi-week effort |
| Core | 200–399 | Senior IC; ≤ 1 week |
| Refinement | 100–199 | Mid-level IC; ≤ 3 days |
| Polish | < 100 | Junior IC or pairing; ≤ 1 day |

---

# Section A — The Premium Revamp (x1)

## PRX-25-EPIC-01 · `vaultbrain-client` production-grade adapter 🔒

| Field | Value |
|-------|-------|
| Lane | portfolio-wide (consumed by A, B, C, D, E, W, L, B′) |
| Owner role | Implementer (Platform) + Reviewer: Architect + Security |
| Channel | `adapters` |
| Surface | `packages/adapters/vaultbrain-client/` |
| Target | Phase-0 stub → production-grade async client with full WS lifecycle |
| Effort | 8–13 ideal-engineer-days |
| ICE | 9 × 7 × 5 = **315** (Core, upper end) |
| Source ADRs | ADR-0003 (superseded), ADR-0008 (extension), ADR-0014 (contracts) |
| Telemetry | every `ProgressionEvent`, `FocusSession`, `Streak`, `CognitiveProfile`, `Manuscript` op flows through this |

### Acceptance criteria (all required)

- [ ] **Real HTTP surface** — `currentUser()`, `getProgression()`,
      `startSession()`, `completeSession()`, `recordEvent(payload)`,
      `getStreaks()`, `getCognitiveProfile()`, `upsertManuscript()`,
      `listCards()`, `recordReview()` — each typed end-to-end against
      `contracts/openapi/njz-rat-os.yaml`.
- [ ] **WebSocket lifecycle** — connect / authenticate / heartbeat /
      reconnect (capped exponential backoff: 1 s → 2 → 4 → 8 → 16 → 30) /
      graceful close. State machine documented in the package's
      `README.md`.
- [ ] **Offline queue** — events recorded while offline persist to
      IndexedDB via `idb-keyval`; replayed FIFO on reconnect; idempotency
      keys on every event payload (UUID v7 by default).
- [ ] **Schema validation** — every inbound payload runs through a `zod`
      schema; failures surface as typed `VaultbrainContractError` with
      enough context for a Sentry breadcrumb.
- [ ] **Observability** — emit `vaultbrain-client:request` /
      `vaultbrain-client:response` / `vaultbrain-client:error` /
      `vaultbrain-client:ws-state-change` events on a shared event bus
      so each lane's analytics consumer can subscribe.
- [ ] **Test matrix** — unit (zod schemas, queue order, backoff curve),
      integration (msw-mocked happy path + 4 failure modes), contract
      (typecheck against generated types from openapi.yaml).
- [ ] **Migration path** — Phase-1 lanes that already consumed the stub
      continue compiling. The stub's named exports become re-exports of
      the new implementation; no caller edits required to land the lift.
- [ ] **Threat model delta** — auth-token storage (in-memory only;
      refresh via HttpOnly cookie); WS auth via JWT on connect;
      payload-side encryption deferred to ADR follow-up if surfaced.

### Sub-tasks (commit-shape)

- [ ] T1: Codegen scaffold from `contracts/openapi/njz-rat-os.yaml` →
      `src/generated/`; commit generated types as the contract source.
- [ ] T2: HTTP client layer — `fetch` wrapper with retry, abort signal,
      auth-header injection; zod-parse every response.
- [ ] T3: WS client layer — `WebSocket` wrapper with the lifecycle state
      machine (xstate v5; reuse the focus-engine pattern); subscribe API.
- [ ] T4: Offline queue layer — idb-keyval store, replay on connect,
      conflict resolution policy (last-write-wins for profile; append-only
      for events).
- [ ] T5: Observability surface — typed event-bus exports, Sentry
      breadcrumb adaptor, debug log toggle via `localStorage.NJZ_DEBUG`.
- [ ] T6: Tests + contract regression + README + DECISION_LOG entry.

### Dependencies

- Lane F upstream coordination Thread 2 (vaultbrain extension) must be
  at least at **endpoint freeze** (schemas + endpoint list agreed
  upstream). Implementation can start against the openapi.yaml once
  endpoints are frozen even if the upstream server isn't shipped — msw
  mocks fill the gap.
- ADR-0008 stays Accepted; Option B fallback path documented in the
  client's README (env-var switch flips to `services/rat-os-state`).

### Out of scope (this item)

- Payload-side encryption (would need new ADR).
- Cross-device CRDT merge (manuscript collab is single-author Phase 2).
- Calendar webhook ingestion (Lane D's territory).

---

# Section B — Minor Refinement Sprints (x2)

## PRX-25-SPRINT-01 · Editor-stack benchmark (W) 🧪

| Field | Value |
|-------|-------|
| Lane | W (Writing Space) |
| Owner role | Implementer + Reviewer: Designer |
| Channel | `packages-engines` (writing) + sandbox harness in `apps/web` |
| Surface | `packages/@njz-os/writing/bench/` + `apps/web/src/dev/editor-bench/` |
| Target | settle ADR-0015 with empirical evidence, not opinion |
| Effort | 3 ideal-engineer-days |
| ICE | 6 × 9 × 8 = **432** (Keystone for the lane's risk surface) |
| Hypothesis | Tiptap (recommended in EXPANDED.md §11) beats ProseMirror-raw + Lexical on mobile-keyboard latency at the chapter sizes our P95 user produces (≤ 80 KB markdown) |
| Ship rule | If Tiptap wins ≥ 2 of: { time-to-first-keystroke, p95 keystroke-to-paint, bundle-size, iOS-Safari quirks count } at the chapter size — ADR-0015 records "Tiptap"; else escalate. |

### Acceptance criteria

- [ ] Three sandbox routes mounted under `apps/web/src/dev/editor-bench/{tiptap,prosemirror,lexical}.tsx`, each loading the same 80 KB markdown fixture.
- [ ] Measurement harness (`bench/index.ts`) records: TTI, keystroke-to-paint p50/p95/p99 (1 000 keystrokes scripted), `performance.measure()` for paste/undo/format-toggle ops, devtools memory snapshot at idle + after editing.
- [ ] Mobile run on iPhone 12 Safari + Pixel 6 Chrome with the same harness.
- [ ] Benchmark report committed to `docs/dev-reports/DR-W-editor-bench.md` with raw numbers + recommended ADR-0015 verdict.
- [ ] Bench routes guarded behind `NJZ_DEV_BENCH` env flag; do not ship to production builds.

### Dependencies

- None on `main`. PR #25's docs are sufficient.

## PRX-25-SPRINT-02 · SM-2 vs FSRS comparative analysis (L) 🧪

| Field | Value |
|-------|-------|
| Lane | L (Micro-Learning) |
| Owner role | Implementer + Reviewer: Data Engineer |
| Channel | `packages-engines` (learning-cards) |
| Surface | `packages/@njz-os/learning-cards/bench/` |
| Target | settle SM-2 (EXPANDED.md §4 recommendation) vs FSRS-5 with offline simulation on a synthetic cohort |
| Effort | 4 ideal-engineer-days |
| ICE | 7 × 6 × 7 = **294** (Core) |
| Hypothesis | SM-2 + interval-jitter ±10% retains ≥ 92% of FSRS-5's review efficiency at < 30% of FSRS-5's per-review compute and parameter complexity for our Phase-2 cohort (N < 50 cards/user/week) |
| Ship rule | If SM-2 retains ≥ 90% efficiency at < 50% complexity → ship SM-2 + jitter; else open ADR-0020 (FSRS adoption). |

### Acceptance criteria

- [ ] Synthetic cohort generator simulates 1 000 users × 365 days × 50 cards/user with three forgetting-curve shapes (steep, medium, shallow).
- [ ] Both algorithms run side-by-side over the cohort; metrics: total reviews, mean retention at 7 / 30 / 90 days, time-to-mastery, review-burden p50/p95.
- [ ] Report committed to `docs/dev-reports/DR-L-srs-bench.md`; raw CSV outputs under `bench/output/` (gitignored except for the summary).
- [ ] Verdict feeds the ADR-0016 / 0017 sequencing decision (per EXPANDED.md §11 open question).

### Dependencies

- None on `main`.

---

# Section C — Performance changes (x3)

## PRX-25-PERF-01 · Bundle-size budget instrumentation 🔒

| Field | Value |
|-------|-------|
| Lane | W (primary) + L + B′ (secondary; benefits all) |
| Owner role | Implementer + Reviewer: Architect |
| Channel | `web-app` + `framework` |
| Surface | `apps/web/vite.config.ts`, `tools/bundle-budget/`, `.github/workflows/bundle-budget.yml` |
| Effort | 2 ideal-engineer-days |
| ICE | 8 × 8 × 7 = **448** (Keystone) |

### Acceptance criteria

- [ ] Per-route budget table committed at `tools/bundle-budget/budgets.json` covering: `/`, `/focus`, `/sound`, `/world`, `/blocker`, `/write`, `/learn`, `/brain`.
- [ ] Initial budgets: marketing routes ≤ 110 KB gz; webapp shell ≤ 180 KB gz; per-module first-paint chunk ≤ 90 KB gz; per-route TTI budget ≤ 2.5 s on Moto G4 throttled.
- [ ] CI workflow runs `vite build --report` + `bundle-buddy` (or `rollup-plugin-visualizer` JSON output); diffs vs the budget; fails the run on hard breach; warns on soft (≥ 80% of budget).
- [ ] Report uploaded as a workflow artifact; PR comment posted with the delta vs `main` (via `pr_comment` action).
- [ ] Runbook at `docs/operations/RUNBOOKS/bundle-budget.md` describing how to triage a breach (split chunk, defer route, swap dependency).

## PRX-25-PERF-02 · Lighthouse CI integration

| Field | Value |
|-------|-------|
| Lane | W + L + B′ (and retro-applies to A/B/C/D/E once they land) |
| Owner role | Implementer + Reviewer: Designer |
| Channel | `framework` + `web-app` |
| Surface | `.github/workflows/lighthouse-ci.yml`, `lighthouserc.json` |
| Effort | 1.5 ideal-engineer-days |
| ICE | 7 × 8 × 8 = **448** (Keystone) |

### Acceptance criteria

- [ ] Lighthouse CI runs on every PR head against a preview deployment of `apps/web`.
- [ ] Targets per the Phase-1 exit criteria: perf ≥ 85, a11y ≥ 85, PWA ≥ 85, best-practices ≥ 90, SEO ≥ 90 on every main route.
- [ ] Trend stored via `@lhci/server` (or LHCI's GitHub action artifact retention) for 30-day rolling comparison.
- [ ] PR fails on regression > 5 points or below absolute target; warning at 2-point regression.
- [ ] Per-route audit recipes documented in `docs/operations/RUNBOOKS/lighthouse-ci.md`.

## PRX-25-PERF-03 · Animation-frame budget audit (B′)

| Field | Value |
|-------|-------|
| Lane | B′ (Brain Training — games render at 60 fps target) |
| Owner role | Implementer + Reviewer: Critic |
| Channel | `packages-engines` (brain-training when scaffolded) + `web-app` |
| Surface | `packages/@njz-os/brain-training/perf/` + dev overlay in webapp |
| Effort | 2 ideal-engineer-days |
| ICE | 6 × 7 × 6 = **252** (Core) |

### Acceptance criteria

- [ ] Per-game frame-time budgeter — each game's tick must complete ≤ 8 ms p50, ≤ 14 ms p95 on Moto G4 throttled.
- [ ] Dev overlay shows the running frame-time graph; toggled by `?bench=1` query param; off in production builds.
- [ ] Vitest perf-mode regression test runs the tick fn 10 000× and asserts mean within budget; fails CI on regression > 15%.
- [ ] Per-game tuning notes documented in `docs/dev-reports/DR-Bprime-frame-budget.md`.

---

# Section D — Group-Portfolio integration patches (x5)

These are the cross-lane refinements that compound: each patch lifts a
seam shared by multiple modules, so the integration cost goes down for
every future lane.

## PRX-25-PATCH-01 · Standardised event-emitter surface

| Field | Value |
|-------|-------|
| Lanes | W, L, B′ (and retro to A, B, C, D, E) |
| Owner role | Implementer + Reviewer: Architect |
| Channel | `packages-engines` (core) |
| Surface | `packages/@njz-os/core/src/events.ts` |
| Effort | 1.5 ideal-engineer-days |
| ICE | 7 × 8 × 8 = **448** (Keystone) |

### Acceptance criteria

- [ ] One canonical `EventBus<TEventMap>` exported from `@njz-os/core`.
- [ ] All seven module engines (focus, audio, polyworld, blocker,
      writing, learning-cards, brain-training) consume the same bus.
- [ ] Type-safe event names — registry in `events.ts` matches the
      `.agents/SCHEMA_REGISTRY.md` `Event` section.
- [ ] No more than one bus per browser session; cross-module subscribers
      tested via a Vitest integration suite.
- [ ] Docs added to `docs/architecture/DATA_FLOW.md` (an event-flow
      diagram in ASCII).

## PRX-25-PATCH-02 · Shared progression-state hook

| Field | Value |
|-------|-------|
| Lanes | W + L + B′ (consume); A + C produce |
| Owner role | Implementer + Reviewer: Designer |
| Channel | `packages-engines` (progression) + `web-app` |
| Surface | `packages/@njz-os/progression/src/useProgression.ts` |
| Effort | 1 ideal-engineer-day |
| ICE | 6 × 8 × 8 = **384** (Core, top) |

### Acceptance criteria

- [ ] `useProgression(userId)` returns `{ streak, totalXp, level, recentEvents, isLoading, error }` reading from the vaultbrain-client cache (TanStack Query, 60 s stale).
- [ ] Optimistic updates on `recordEvent` — the cache writes through immediately; reconciles on WS confirmation.
- [ ] Used by W's Manuscript-list view (display streak), L's review session (XP gained on review), B′'s Cognitive-Profile header.
- [ ] One Vitest integration test mounts the hook in a `QueryClientProvider` against an msw-mocked vaultbrain.

## PRX-25-PATCH-03 · Cross-lane error boundary

| Field | Value |
|-------|-------|
| Lanes | all 8 |
| Owner role | Implementer + Reviewer: Security |
| Channel | `web-app` + `ui` |
| Surface | `packages/@njz-os/ui/src/ErrorBoundary.tsx` |
| Effort | 1 ideal-engineer-day |
| ICE | 6 × 9 × 9 = **486** (Keystone) |

### Acceptance criteria

- [ ] Module routes wrapped in a typed `ErrorBoundary` with: friendly fallback UI, recovery CTA ("retry", "back to home"), Sentry breadcrumb capture, no leak of PII to the user-facing surface.
- [ ] Vitest test forces an error in a child component and asserts the fallback renders + Sentry breadcrumb fires.
- [ ] Per-lane fallback copy customisable via prop; defaults documented in `packages/@njz-os/ui/README.md`.

## PRX-25-PATCH-04 · Unified telemetry pipeline

| Field | Value |
|-------|-------|
| Lanes | W + L + B′ (primary); retro-applies |
| Owner role | Implementer + Reviewer: Data Engineer |
| Channel | `packages-engines` (analytics) |
| Surface | `packages/@njz-os/analytics/src/pipeline.ts` |
| Effort | 2 ideal-engineer-days |
| ICE | 7 × 7 × 7 = **343** (Core) |

### Acceptance criteria

- [ ] `track(eventName, payload)` enqueues to an in-memory ring (cap 200 events) then flushes batched POSTs to vaultbrain `/events/batch` every 5 s or on `pagehide`.
- [ ] Dropped-event metric exposed (overflow counter) so QA can validate batch size.
- [ ] PII scrubber runs before the batch leaves the browser — `email`, `displayName`, `manuscriptBody`, `cardFront`, `cardBack` are stripped or hashed per `.agents/CONTEXT_DATA_ENGINEER.md`.
- [ ] Events conform to `contracts/events/v1/*.json` (new dir; bind to the SCHEMA_REGISTRY).

## PRX-25-PATCH-05 · Shared toast/notification surface

| Field | Value |
|-------|-------|
| Lanes | all 8 |
| Owner role | Implementer + Reviewer: Designer |
| Channel | `ui` + `web-app` |
| Surface | `packages/@njz-os/ui/src/toast/` |
| Effort | 1 ideal-engineer-day |
| ICE | 5 × 9 × 9 = **405** (Keystone, lower end) |

### Acceptance criteria

- [ ] Single `<ToastProvider>` mounted at app root; `useToast()` hook returns `notify(message, opts)`.
- [ ] Variants: `info`, `success`, `warning`, `error`; auto-dismiss timings per the design tokens; aria-live polite for non-critical, assertive for error.
- [ ] Stack management — max 3 visible; older auto-shift to history accessible via icon button.
- [ ] Reduced-motion alternative — fades, not slides — honoured automatically when `prefers-reduced-motion: reduce`.

---

# Section E — Functionality / efficiency enhancements (x5)

## PRX-25-ENH-01 · IndexedDB hot-cache for vaultbrain reads

| Field | Value |
|-------|-------|
| Lane | portfolio-wide |
| Owner role | Implementer + Reviewer: Architect |
| Channel | `adapters` |
| Surface | `packages/adapters/vaultbrain-client/src/cache/` |
| Effort | 2 ideal-engineer-days |
| ICE | 7 × 7 × 7 = **343** (Core) |

### Acceptance criteria

- [ ] Read-through cache backed by IndexedDB; TTL per resource: profile 5 min, progression 60 s, manuscripts 10 min, cards 5 min.
- [ ] Cache-bust on WS push for the affected resource (subscribed via the standardised event-emitter; PATCH-01 dep).
- [ ] First-paint after warm cache feels instantaneous (< 50 ms to first useful render of `/learn`, `/write`, `/brain` home views).
- [ ] Vitest integration test asserts warm vs cold timings on jsdom (synthetic but trend-positive).

## PRX-25-ENH-02 · Optimistic UI updates

| Field | Value |
|-------|-------|
| Lanes | W (manuscript autosave), L (review submit), B′ (game-result record) |
| Owner role | Implementer + Reviewer: Designer |
| Channel | `web-app` |
| Surface | `apps/web/src/modules/{writing,micro-learning,brain-training}/mutations.ts` |
| Effort | 2 ideal-engineer-days |
| ICE | 6 × 7 × 8 = **336** (Core) |

### Acceptance criteria

- [ ] Mutations write the optimistic state immediately; reconcile on WS confirm (PATCH-02 dep).
- [ ] On error: rollback + toast (PATCH-05 dep) with retry CTA; offline queue (vaultbrain-client EPIC-01) catches the rest.
- [ ] Vitest test asserts the optimistic-then-rollback path renders correct UI states.

## PRX-25-ENH-03 · Streaming SSR for marketing pages (L)

| Field | Value |
|-------|-------|
| Lane | L (the Micro-Learning marketing page; benefits SEO) |
| Owner role | Implementer + Reviewer: Architect |
| Channel | `site` |
| Surface | `apps/site/src/app/modules/micro-learning/page.tsx` |
| Effort | 1 ideal-engineer-day |
| ICE | 5 × 7 × 9 = **315** (Core, lower) |

### Acceptance criteria

- [ ] Above-the-fold renders < 200 ms; below-the-fold streams; verified via `curl --no-buffer` + Lighthouse waterfall.
- [ ] OG tags + JSON-LD structured data complete (`SoftwareApplication` schema for the module landing pages).
- [ ] No regression on PERF-02 Lighthouse SEO score.

## PRX-25-ENH-04 · Pre-computed cohort percentiles (B′)

| Field | Value |
|-------|-------|
| Lane | B′ |
| Owner role | Implementer + Reviewer: Data Engineer |
| Channel | `packages-engines` (brain-training) + vaultbrain backend |
| Surface | `packages/@njz-os/brain-training/src/percentiles.ts` + upstream cron |
| Effort | 2 ideal-engineer-days |
| ICE | 6 × 6 × 7 = **252** (Core, lower) |

### Acceptance criteria

- [ ] Vaultbrain cron computes per-game cohort percentiles nightly (`p10, p25, p50, p75, p90` by age-bracket × game).
- [ ] Client receives the snapshot on `/users/me/cohort-stats`; renders the user's percentile-band in the Cognitive Profile header.
- [ ] PII-free: only the user's own score vs aggregate; never another user's row.
- [ ] Documented in EXPANDED.md §5 cognitive-profile telemetry follow-up.

## PRX-25-ENH-05 · Shared design-token compile step

| Field | Value |
|-------|-------|
| Lanes | all 8 |
| Owner role | Implementer + Reviewer: Designer |
| Channel | `ui` + `framework` |
| Surface | `packages/@njz-os/ui/tokens/` + `tools/tokens-build/` |
| Effort | 1.5 ideal-engineer-days |
| ICE | 6 × 8 × 8 = **384** (Core, top) |

### Acceptance criteria

- [ ] Single source of truth `tokens.json` (color, spacing, radius, motion, typography); compiles to `.css` (custom properties), `.ts` (typed exports), `.json` (raw).
- [ ] Compile script wired into `pnpm install` postinstall + CI; validator catches off-palette literals in source (lints against hex literals in `*.tsx` that aren't in the token table).
- [ ] Docs `packages/@njz-os/ui/tokens/README.md` documents the editing protocol + accessibility contrast guarantees.

---

# Section F — Sequencing recommendation

The dependency graph below shows what must land first (left) before the
dependent items become tractable (right). ICE ties are broken toward
lower risk / shorter critical path.

```
EPIC-01 (vaultbrain-client) ─┬─▶ ENH-01 (IDB cache)
                             │
                             ├─▶ ENH-02 (optimistic UI)
                             │
                             └─▶ PATCH-04 (telemetry pipeline)

PATCH-01 (event-bus) ────────┬─▶ PATCH-02 (progression hook)
                             │
                             └─▶ ENH-01 (cache-bust signal)

PATCH-05 (toasts) ───────────┬─▶ ENH-02 (rollback UI)

PERF-01 (bundle-budget) ─────┐
PERF-02 (lighthouse CI) ─────┼─▶ gates all other PR merges via CI checks
PATCH-03 (error-boundary) ───┘

SPRINT-01 (editor-bench) ───▶ ADR-0015 (Tiptap default) ───▶ W code starts
SPRINT-02 (SRS bench) ──────▶ ADR-0016/0017 sequence    ───▶ L code starts
PERF-03 (frame-budget) ─────▶ B′ code starts
ENH-04 (cohort percentiles) ▶ B′ first-screen ships
ENH-05 (design tokens) ─────▶ all UI consumers (parallel-safe)
ENH-03 (streaming SSR) ─────▶ /modules/* marketing pages
```

### Recommended order (single-author-per-PR cadence)

1. **PRX-25-PERF-01** — bundle-budget (low-risk infra; gates every later merge).
2. **PRX-25-PERF-02** — Lighthouse CI (same; cheap upfront, dividends compound).
3. **PRX-25-PATCH-01** — event-bus (foundation for PATCH-02 + ENH-01).
4. **PRX-25-EPIC-01** — vaultbrain-client (the keystone; multi-week; unblocks 3 other items).
5. **PRX-25-PATCH-02** — progression hook (consumes EPIC-01 + PATCH-01).
6. **PRX-25-PATCH-03** — error boundary (parallel-safe; ship in any window).
7. **PRX-25-PATCH-05** — toasts (parallel-safe; ENH-02 depends).
8. **PRX-25-PATCH-04** — telemetry pipeline.
9. **PRX-25-SPRINT-01** — editor bench (W gate; offline).
10. **PRX-25-SPRINT-02** — SRS bench (L gate; offline).
11. **PRX-25-ENH-05** — design tokens (parallel-safe; UI consumers).
12. **PRX-25-ENH-01** — IDB hot cache.
13. **PRX-25-ENH-02** — optimistic UI.
14. **PRX-25-ENH-03** — streaming SSR.
15. **PRX-25-PERF-03** — B′ frame-budget (once B′ code begins).
16. **PRX-25-ENH-04** — cohort percentiles (final B′ enhancement).

Total budget if serialised: ≈ 32 ideal-engineer-days. With three
parallel ICs across the three lanes (mature team profile), ≈ 12
calendar days.

# Section G — Cross-cutting risks

| Risk | Likelihood | Impact | Mitigation | Item(s) it touches |
|------|------------|--------|------------|--------------------|
| Vaultbrain upstream Option A stalls | M | H | EPIC-01 ships against the openapi.yaml contract with msw mocks; Option B switch documented in client README; 2-week timer in `.agents/active/upstream-coordination.md` already running | EPIC-01, PATCH-02, PATCH-04, ENH-01, ENH-04 |
| Editor-bench inconclusive | M | M | SPRINT-01 ship rule is strict; on inconclusive, escalate to user with a 1-page summary; default to Tiptap (lowest risk) if forced | SPRINT-01, W code-impl |
| Bundle-budget regression mid-implementation | L | M | PERF-01 budgets are hard CI gates; breach blocks merge; runbook covers triage | every code PR after PERF-01 lands |
| Telemetry pipeline drops events on `pagehide` | M | H | Use `sendBeacon` for the final flush; integration test in a headless browser asserts the beacon fires | PATCH-04 |
| Cohort-percentile feature reveals a small-cohort identification risk | L | H | Aggregate buckets ≥ N=50 per slot; suppress band if fewer; Security review on the cron output schema | ENH-04 |
| Tokens compile step breaks existing CSS module imports | L | L | Compile is additive — old class names continue to work; deprecation warnings on legacy imports for one minor version | ENH-05 |

# Section H — How this document is maintained

- **Append-only after initial merge.** Items can be marked DONE / DEFERRED with a strike-through; do not delete rows.
- **Each item closure** records the PR number + commit SHA in the row's "Acceptance" sub-list + a DECISION_LOG line.
- **New items** added at the bottom of the relevant Section with PRX-25-{SECTION}-NN incremented.
- **Quarterly review** trims completed sections to a 1-sentence summary; rotation maintained at `docs/program-management/PR-25-portfolio-uplift-archive.md` once the live doc grows beyond what a single review session can scan.

# Section I — Pointers

- Source EXPANDED.md docs this plan refines:
  - `docs/modules/writing-space/EXPANDED.md`
  - `docs/modules/micro-learning/EXPANDED.md`
  - `docs/modules/brain-training/EXPANDED.md`
- Phase-1 EXPANDED.md docs (for parity reference):
  - `docs/modules/focus-hero/EXPANDED.md`
  - `docs/modules/soundscapes/EXPANDED.md`
  - `docs/modules/polyco-world/EXPANDED.md`
  - `docs/modules/distraction-blocker/EXPANDED.md`
  - `docs/modules/auth-and-site/EXPANDED.md`
- Source ADRs invoked:
  - ADR-0008 (vaultbrain extension — EPIC-01 prerequisite path)
  - ADR-0014 (contracts vendoring — EPIC-01 consumer surface)
  - ADR-0015 candidate (editor stack — SPRINT-01 ship rule)
  - ADR-0016/0017 candidates (content licensing + illustration hosting — SPRINT-02 ship rule)
  - ADR-0018/0019 candidates (adaptive bounds + cognitive baseline — ENH-04 prerequisite)
- Code-implementation handoff this uplift extends:
  - `.agents/handoff/stage-3-code-implementation-handoff.md`

---

*End of PR-25 portfolio uplift plan. Open follow-up handoff at
`.agents/handoff/pr-25-portfolio-uplift-followup.md` after first three
items close.*
