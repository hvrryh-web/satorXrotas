[Ver001.000]

# Runbook — Bundle budget breach

> **Owner:** Platform · **Trigger:** `bundle-budget` CI job FAIL on a PR
> **Tool:** `tools/bundle-budget/check.mjs` + `tools/bundle-budget/budgets.json`
> **Source item:** PRX-25-PERF-01 in `docs/program-management/PR-25-portfolio-uplift.md`

---

## What the breach means

The CI workflow `Bundle budget` compares each app route's first-paint
chunk (gzipped) against the budgets declared in
`tools/bundle-budget/budgets.json`. A `FAIL` means a chunk crossed its
hard limit. A `WARN` means it crossed the soft limit (80% of hard) — the
PR still merges but the next breach will block it.

---

## Triage flow

### 1. Confirm the breach is real

Download the `bundle-budget-report` artifact from the failing run. Look
for the offending row — `STATUS = FAIL`, the measured bytes, and the
limit. Sanity-check by rebuilding locally:

```bash
pnpm install
pnpm build
node tools/bundle-budget/check.mjs
```

If the local run agrees, proceed.

### 2. Localise the regression

```bash
git fetch origin main
git diff origin/main -- packages/@njz-os apps/web/src apps/site/src \
  | head -200
```

Look for dependency additions in `package.json` files, new
`import { … } from '<heavy-lib>'`, or new top-level `import` statements
in route components that should have been lazy-loaded.

### 3. Pick a fix path

| Cause | Fix |
|-------|-----|
| New heavy dependency added to top-level import | `React.lazy` the consumer; route-level dynamic import; ensure the chunk is only loaded on its route |
| Dependency duplicated across modules | Hoist to a shared package or accept the dup but raise the budget in `budgets.json` with rationale |
| Token table inflation (ENH-05) | The token compile step should split CSS from TS exports — verify the .ts file isn't pulling the full CSS string at runtime |
| Adapter import bloat | `vaultbrain-client` (EPIC-01) should be tree-shakable; check for `export * from './heavy-module'` patterns |
| Polyfill added by Vite target | Confirm `vite.config.ts` `build.target = 'es2022'` (already pinned) |

### 4. If the budget itself needs to change

Reach this only after fix paths above don't apply. Open a tiny
companion PR:

```bash
# In budgets.json, raise the route's hardLimit + softLimit.
# Always raise softLimit to keep the 80% ratio.
```

The PR description must include:

- the before/after bytes
- the cause (one paragraph)
- the alternative paths considered + why they were rejected
- the next PRX-25 enhancement that will bring it back down (if any)

A budget raise is a load-bearing decision — Architect review required.

### 5. Soft-limit handling

If your PR triggers `WARN` on a route, it merges, but:

- Drop a `bundle-budget` comment on the PR noting "this is a soft-limit
  warning; the next breach will block."
- Open a follow-up issue if the route is trending upward over the prior
  3 PRs (look at the report artifact retention).

---

## Re-running the check

After local fixes:

```bash
rm -rf apps/web/dist apps/site/.next
pnpm build
node tools/bundle-budget/check.mjs
```

Push; CI re-runs the workflow.

---

## When to refresh the budgets

- **Major device-baseline shift** (e.g., Moto G4 retires; new P95 device
  is faster) — update budgets downward.
- **New module ships** (Phase 1 lane closes; Phase 2 lane closes) —
  add a row, set initial budget at the route's measured first-paint
  bytes + 15% headroom.
- **Major dependency upgrade** (React 19 → 20, Vite 6 → 7) — measure
  baseline shift, decide whether to absorb or fix.

## Known limitations

- **Site routes use total-chunk-sum attribution.** Next.js 15 ships
  multiple shared chunks (framework, react, polyfills, app-router
  shared); the validator currently reports the sum of all chunks under
  `.next/static/chunks/` as the per-route number. This overstates the
  actual first-paint download for individual pages (Next.js streams the
  HTML + critical CSS first; JS chunks are deferred). Follow-up to
  refine the site attribution: walk `.next/app-build-manifest.json` or
  `.next/required-server-files.json` to attribute per-route. Tracked
  internally as a known limitation; budgets adjusted upward
  (240→280 KB gz) to reflect framework baseline rather than wishful
  thinking.
- **Webapp per-route chunks are accurate** — Vite emits per-entry +
  per-React.lazy chunks; the regex-based attribution in `check.mjs`
  matches them correctly.
- **SKIP rows** report zero measurements because the relevant route
  hasn't shipped its code yet (Phase-1 lanes A/B/C/D and Phase-2 lanes
  W/L/B′). Budgets remain in place to detect regressions when the lane
  code lands.

---

## Cross-references

- `tools/bundle-budget/check.mjs` — the script the CI runs
- `tools/bundle-budget/budgets.json` — the budget table
- `tools/bundle-budget/check.test.mjs` — self-test (runs in CI before the
  real check, validates the validator)
- `.github/workflows/bundle-budget.yml` — CI workflow
- `docs/program-management/PR-25-portfolio-uplift.md` § PRX-25-PERF-01 —
  acceptance criteria
- ROOT_AXIOMS/02_STANDARDS/00-code.md — performance discipline
