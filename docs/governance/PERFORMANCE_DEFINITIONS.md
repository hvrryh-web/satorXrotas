[Ver001.000]

# Performance Definitions — NJZ RAT-OS

> **Purpose:** concrete (not aspirational) per-lane performance budgets
> with thresholds, sources, refresh cadence, and how a regression is
> detected + handled. Replaces ad-hoc "Lighthouse ≥ 85" mentions
> scattered through EXPANDED.md docs with a single referable surface.
> **Status:** active baseline · refreshed quarterly.
> **Authored:** 2026-05-30 (post Phase-1 lane sweep).

---

## 1. Universal envelope

Targets apply to:

- Production builds (`pnpm build`)
- Moto G4 throttled (4× CPU slowdown, 4G), unless flagged otherwise
- p95 percentile across the trailing 10 measurement runs
- Measured by the CI workflows named in each row

---

## 2. Per-route bundle budgets (gzipped first-paint chunk)

| Route | Hard | Soft | Source | Notes |
|-------|------|------|--------|-------|
| `site://` (marketing home) | 280 KB | 240 KB | `tools/bundle-budget/budgets.json` | Next.js 15 framework baseline; per-page attribution follow-up |
| `site:/modules` | 280 KB | 240 KB | same | streaming SSR reduces TTI not bundle |
| `web://` (shell) | 180 KB | 147 KB | same | includes React + router + query |
| `web:/focus` | 90 KB | 73 KB | same | xstate-free reducer keeps it tight |
| `web:/sound` | 90 KB | 73 KB | same | audio-engine defer-loadable |
| `web:/blocker` | 90 KB | 73 KB | same | |
| `web:/write` | 120 KB | 98 KB | same | editor stack inflates; pending ADR-0015 |
| `web:/learn` | 90 KB | 73 KB | same | |
| `web:/train` | 100 KB | 81 KB | same | five games lazy-loaded per game |
| `web:/world` | 100 KB | 81 KB | same | Canvas 2D renderer + pixel-art loader |

Soft = 80 % of hard. Soft → `WARN`, hard → `FAIL` in
`.github/workflows/bundle-budget.yml`.

---

## 3. Per-route Lighthouse targets

| Category | Threshold | Mode | Source |
|----------|-----------|------|--------|
| Performance | ≥ 85 | warn | `lighthouserc.json` |
| Accessibility | ≥ 85 | warn | same |
| Best Practices | ≥ 90 | warn | same |
| SEO | ≥ 90 | warn | same |
| PWA | not asserted in Phase 1 | — | Phase 2 manifest + SW |

Tighten `warn → error` after 3 consecutive green main-branch runs.
Runbook: `docs/operations/RUNBOOKS/lighthouse-ci.md`.

---

## 4. Per-lane runtime budgets

### Lane A — Focus Engine

| Metric | Target | Measurement | Refresh |
|--------|--------|-------------|---------|
| Tick interval | 500 ms | `tickIntervalMs` in `useFocusSession.ts` | per session |
| State-machine reducer | < 1 ms p99 | `machine.test.ts` perf-mode | per-PR |
| Drift after 25-min session (clock-injected) | ≤ 100 ms cumulative | machine.test (TODO follow-up) | per-PR |
| Boundary-callback fan-out | < 5 ms p95 | useFocusSession test (TODO) | per-PR |

### Lane B — Audio Engine

| Metric | Target | Measurement | Refresh |
|--------|--------|-------------|---------|
| Crossfade loop-boundary discontinuity | ≤ 0.5 dB | `scheduler.test.ts` | per-PR |
| AnalyserNode FFT size | 2048 | `graph.ts` | static |
| Master limiter threshold | -10 dBFS | `graph.ts` | static, per ADR-0010 |
| Master limiter ratio | 20:1 | `graph.ts` | static, per ADR-0010 |
| Binaural carrier range | 50-800 Hz | `binaural.validatePreset` | static |
| Deep Canvas painter (Task B5 future) | ≥ 30 fps on Moto G4 throttled | bench (TODO) | future |

### Lane C — PolyCo.World

| Metric | Target | Measurement | Refresh |
|--------|--------|-------------|---------|
| Tile size | 16 px | `iso.TILE_W` | static, per ADR-0005 |
| Iso ratio | 2:1 | `iso.TILE_H = TILE_W / 2` | static |
| Renderer 60 fps with 100 sprites (Moto G4) | ≥ 60 fps | bench (TODO, with C1 asset pipeline) | future |
| Scene parse failure surfacing | `SceneParseError` thrown, never silent | `scene-loader.test.ts` | per-PR |

### Lane D — Distraction Blocker

| Metric | Target | Measurement | Refresh |
|--------|--------|-------------|---------|
| Schedule resolver decision | < 5 ms p95 | `schedule.test.ts` (perf-mode follow-up) | per-PR |
| Focus score formula | 0..100 clamped | `schedule.test.ts` | per-PR |
| Cross-midnight DST handling | every test passes 2× per year (March + November DST shifts) | `schedule.test.ts` | static |

### Lane E — Auth + Site

| Metric | Target | Measurement | Refresh |
|--------|--------|-------------|---------|
| Marketing home TTFB | ≤ 200 ms on Vercel Edge | Lighthouse waterfall | per-PR |
| Magic-link request → email delivery | < 30 s p95 | upstream Supabase metrics (when wired) | future |
| Passkey enrollment success rate | ≥ 95 % | upstream Supabase metrics (when wired) | future |
| Onboarding completion rate | ≥ 80 % start → finish | analytics pipeline (when wired) | future |

### Lane F — Coordination

| Metric | Target | Measurement | Refresh |
|--------|--------|-------------|---------|
| Contracts drift detection | weekly | `.github/workflows/contracts-drift.yml` | weekly |
| Drift triage SLA | open follow-up within 1 business day of drift report | manual | weekly |

---

## 5. Adapter performance

### `vaultbrain-client`

| Metric | Target | Measurement | Refresh |
|--------|--------|-------------|---------|
| Retry attempts (GET / idempotent) | ≤ 4 | `http.ts` `DEFAULT_RETRY` | static |
| Backoff curve | 500 ms × 2ⁿ, capped at 8 s | same | static |
| Schema-parse coverage | 100 % of HTTP responses | `client.test.ts` | per-PR |
| Warm-cache read (IDB) | < 50 ms p95 | future bench | future |
| Offline-queue enqueue latency | < 10 ms p95 | future bench | future |

### `identity-client`

| Metric | Target | Measurement | Refresh |
|--------|--------|-------------|---------|
| Mock provider round-trip | < 5 ms p95 | `mock.test.ts` | per-PR |
| Tier check (cached) | < 1 ms p95 | future bench | future |

---

## 6. Test footprint expectations

| Surface | Minimum tests | Rationale |
|---------|---------------|-----------|
| Per pure-TS module exporting > 3 functions | ≥ 1 test file with ≥ 5 tests | mechanical correctness floor |
| Per React component with branching state | ≥ 1 reducer/hook test (no DOM mount required) | logic separable from view |
| Per zod schema added | ≥ 3 tests: valid input, missing required, out-of-range | parse-mismatch surfaces |
| Per HTTP method on an adapter | ≥ 4 tests: happy, retry, schema fail, network fail | typed-error coverage |

Current totals (2026-05-30, `main`):

| Package | Tests | Status |
|---------|-------|--------|
| `@njz-os/core` | 10 | green |
| `@njz-os/ui` | 10 | green |
| `@njz-os/focus-engine` | 33 | green |
| `@njz-os/audio-engine` | 27 | green |
| `@njz-os/polyworld` | 22 | green |
| `@njz-os/pixel-art` | 7 | green |
| `@njz-os/analytics` | 7 | green |
| `@njz-os/learning-cards` | 7 | green |
| `@njz-os/adapters-identity-client` | 10 | green |
| `@njz-os/adapters-vaultbrain-client` | 16 | green |
| **TOTAL** | **149** | **all green** |

---

## 7. Refresh cadence

| Cadence | What gets refreshed | By whom |
|---------|---------------------|---------|
| Per-PR | Bundle-budget + Lighthouse-CI tables auto-checked by CI | CI |
| Per-lane closure | Lane runtime budgets re-baselined | Lane owner |
| Quarterly | Universal envelope + test-footprint floor reviewed | Coordinator |
| At every major dep upgrade (React 19 → 20, Vite 6 → 7) | All bundle budgets re-baselined | Architect |

---

## 8. Regression handling

| Severity | Trigger | Action |
|----------|---------|--------|
| WARN | Soft-limit breach (≥ 80 % of hard) | PR comment + follow-up issue if trend > 3 PRs |
| FAIL | Hard-limit breach | CI blocks; runbook triage; either fix or raise budget with documented rationale per `docs/operations/RUNBOOKS/bundle-budget.md` §"If the budget itself needs to change" |
| Major | Lighthouse perf < 70 OR test footprint shrinks > 10 % | Coordinator escalates; PR cannot merge without 2 reviewers |

---

## 9. Cross-references

- `tools/bundle-budget/budgets.json` — machine-readable source of §2.
- `lighthouserc.json` — machine-readable source of §3.
- `docs/operations/RUNBOOKS/bundle-budget.md` — triage runbook.
- `docs/operations/RUNBOOKS/lighthouse-ci.md` — triage runbook.
- `docs/governance/TASK_FORMAT_CONVENTION.md` — task-level evidence schema includes `budgetImpact` block.

---

*Living document. Updates require a `chore(governance)` PR + DECISION_LOG entry.*
