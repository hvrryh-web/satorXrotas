[Ver001.000]

# Handoff — PR-25 Portfolio Uplift Follow-up

**Date:** 2026-05-30
**Author:** claude-opus-4.7 (orchestrator)
**Status:** ready to pick up
**Audience:** the next session driving any of the 16 enterprise refinement
items enumerated in `docs/program-management/PR-25-portfolio-uplift.md`

---

## Where you are picking up

PR #25 merged the documentation contract for W (Writing Space), L
(Micro-Learning), B′ (Brain Training) **plus** the enterprise
refinement plan at `docs/program-management/PR-25-portfolio-uplift.md`
that layers 16 ICE-scored work items on top of the EXPANDED.md base.

Each EXPANDED.md now carries a §12 pointer at the bottom that names
the specific work items applicable to that lane, so a fresh subagent
reading one EXPANDED.md immediately sees both the base contract *and*
the refinement plan.

## What you do in **this** session

**Pick one work item from `docs/program-management/PR-25-portfolio-uplift.md`
and ship it.**

Recommended next item (per the doc's §F sequencing): pick the
highest-ICE unblocker that is *not* yet started, working roughly in
this order:

1. **PRX-25-PERF-01** — bundle-size budget instrumentation (ICE 448; gates every later merge).
2. **PRX-25-PERF-02** — Lighthouse CI integration (ICE 448; same).
3. **PRX-25-PATCH-01** — standardised event-emitter surface (ICE 448; foundation for PATCH-02 + ENH-01).
4. **PRX-25-PATCH-03** — cross-lane error boundary (ICE 486; parallel-safe).
5. **PRX-25-EPIC-01** — vaultbrain-client production-grade lift (ICE 315; multi-week keystone).
6. … and onward per the doc's §F ordered list.

If multiple items at the same priority are tractable in this session,
pick the one whose dependencies are most clearly satisfied on the
current `main`. Defer items whose preconditions are not yet landed.

### Per-item strategy

1. **Branch:** `git checkout -b feat/prx-25-<item-id-lower-kebab>` from
   `main` (e.g. `feat/prx-25-perf-01-bundle-budget`).
2. **Read these files (in order):**
   - `docs/program-management/PR-25-portfolio-uplift.md` — find your item
     by ID; read every field in its table + acceptance criteria.
   - The lane's EXPANDED.md if your item is lane-scoped (W, L, or B′).
   - `.agents/AGENT_CONTRACT.md`.
   - Source ADRs invoked by your item (see §I Pointers in the uplift doc).
3. **Work the acceptance criteria as the task list.** Each criterion
   is one commit-shape unit. Don't bundle criteria into a single commit.
4. **Universal success per criterion:** `pnpm typecheck` + `lint` +
   `test` + `node tools/doc-tier-check/index.mjs` all green, plus the
   item-specific criteria (telemetry impact assessed, threat-model
   delta documented if applicable, perf budget honoured).
5. **Stop after each clean commit** if budget is thin.
6. **Open PR** when the item is shipped (or your achievable subset of
   criteria is shipped). Title: `[<channel>] PRX-25-<id> — <title>`.
   Body references the uplift doc + the item ID + completed criteria
   + any deferred criteria.
7. **Append `.agents/DECISION_LOG.md`** with one line on item close
   (date · agent · area · one-sentence decision → PRX-25-…).
8. **Add a row to `.agents/phase-logbooks/PHASE-1-LOGBOOK.md`** (or
   `PHASE-2-LOGBOOK.md` once that file opens) noting the item's
   landing.

### What "implementation" means for the portfolio uplift items

For each item you'll typically add files to:

- `packages/@njz-os/<package>/src/` — for engine-level work (PATCH-01
  event bus, PATCH-02 progression hook, PATCH-04 telemetry pipeline,
  ENH-05 design tokens, PERF-03 frame budget).
- `packages/adapters/<adapter>/src/` — for adapter-layer work (EPIC-01
  vaultbrain-client lift, ENH-01 IDB hot cache).
- `apps/web/src/` — for app-level work (PATCH-03 error boundary,
  PATCH-05 toasts, ENH-02 optimistic UI).
- `apps/site/src/app/` — for marketing work (ENH-03 streaming SSR).
- `tools/` + `.github/workflows/` — for CI / infra work (PERF-01
  bundle budget, PERF-02 Lighthouse CI).
- `packages/@njz-os/<package>/bench/` + `docs/dev-reports/` — for
  benchmark work (SPRINT-01 editor, SPRINT-02 SRS, ENH-04 cohort
  percentiles).

You may NOT (unchanged from prior handoff):

- Touch `.agents/PHASE_GATES.md`.
- Modify existing ADRs 0001–0014.
- Cross channel boundaries — each item's table declares its channel(s).
- Bypass pre-commit hooks (`--no-verify`).

## Sequencing within Phase 1 vs Phase 2

The uplift doc's items split cleanly:

- **Phase-1 ready** (can ship before any Phase-1 lane code lands):
  PERF-01, PERF-02, PATCH-01, PATCH-03, PATCH-05, ENH-05.
- **Needs Phase-1 lane(s) shipped first:** PATCH-02 (needs Lane A's
  ProgressionEvent surface), PATCH-04 (needs the events to flow),
  ENH-01 (needs EPIC-01 + PATCH-01), ENH-02 (needs the mutating
  endpoints to exist).
- **Needs the corresponding Phase-2 lane in flight:** SPRINT-01 (W),
  SPRINT-02 (L), PERF-03 (B′), ENH-03 (L), ENH-04 (B′).
- **Phase-spanning keystone:** EPIC-01 (can start against the openapi
  contract with msw mocks regardless of Phase-1 progress).

The recommended order in the uplift doc's §F respects this gating.

## After your session

Choose one:

- **Continue with another uplift item** (next session): pick the next
  highest-ICE unblocker.
- **If you closed an item that completes a "Group" in §F** (all PATCHes,
  all PERFs, all ENHs), update the uplift doc's table to mark the
  group complete and append a DR fragment.
- **If you discovered a new refinement opportunity** while working an
  item: do not expand scope. Append it to the uplift doc as
  `PRX-25-<SECTION>-NN+1` with full table fields and a one-paragraph
  rationale, in a separate small PR.

## Failure modes — what to do

| Symptom | Action |
|---------|--------|
| Session budget exhausted mid-item | Commit the most recent clean criterion; push; open PR with what's done + a follow-up handoff |
| Item's dependencies not landed | Stop; pick a different unblocked item; surface the dependency gap in this handoff's notes section below |
| Acceptance criterion turns out to be wrong / impossible | Surface to user via `AskUserQuestion`; do not silently amend the criterion |
| Universal success criterion red | Fix the root cause; do not bypass; if can't fix, open a `BLOCKED` follow-up handoff |
| Cross-item scope creep | Resist; split into a follow-up item appended to the uplift doc |

## What's durable on `main` after PR #25 merges

| Item | Status |
|------|--------|
| ADR-0001 .. ADR-0014 | Accepted; on `main` |
| All 8 EXPANDED.md docs | On `main` (5 from PR #24, 3 from PR #25) |
| `docs/program-management/PR-25-portfolio-uplift.md` | On `main` |
| `.doc-tiers.json` T1 includes `docs/program-management/` | On `main` |
| `.doc-registry.json` routes "program management" queries | On `main` |
| Lane F foundational (contracts vendoring + drift CI) | On `main` (PR #21) |

## Quick-start commands

```bash
cd /home/user/satorXrotas
git checkout main
git pull origin main

# Pick your item ID from the uplift doc:
ITEM=prx-25-perf-01-bundle-budget   # example
git checkout -b feat/${ITEM} main

# Read the relevant uplift doc section:
sed -n '/^## PRX-25-PERF-01/,/^## PRX-25/p' docs/program-management/PR-25-portfolio-uplift.md

# Implement against acceptance criteria.
# Universal verification before each commit:
node tools/doc-tier-check/index.mjs
pnpm --filter @njz-os/<package> typecheck
pnpm --filter @njz-os/<package> test --passWithNoTests
pnpm --filter @njz-os/<package> lint

# Open PR:
git push -u origin feat/${ITEM}
# Then mcp__github__create_pull_request from the agent harness.
```

## Sign-off when you finish

1. Append `.agents/DECISION_LOG.md` per criterion completed (one line each).
2. Open the item PR.
3. If the item appended a new follow-up to the uplift doc, that's a
   separate small PR opened first.
4. Drop a follow-up handoff if your work needs continuation in another
   session.

## Notes section (append-only as you discover things)

*Reserved for items you discover that future sessions should know about.
Append below — do not delete prior notes.*

---

Good luck. Build it once, build it right.
