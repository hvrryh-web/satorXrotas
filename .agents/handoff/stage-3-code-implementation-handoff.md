[Ver001.000]

# Handoff — Stage 3 Code Implementation (Next Session)

**Date:** 2026-05-25
**Author:** claude-opus-4.7 (orchestrator)
**Status:** ready to pick up
**Audience:** the next agent session beginning **code implementation** of
the eight NJZ RAT-OS modules

---

## Where you are picking up

All eight modules now have **implementation-ready expanded
documentation** on `main`:

| Lane | Module | EXPANDED.md | Phase | Source ADR |
|------|--------|-------------|-------|------------|
| A | Focus Hero | `docs/modules/focus-hero/EXPANDED.md` | 1 | ADR-0009 |
| B | Soundscapes + Deep Canvas | `docs/modules/soundscapes/EXPANDED.md` | 1 | ADR-0006 + 0010 |
| C | PolyCo.World + Asset Pipeline | `docs/modules/polyco-world/EXPANDED.md` | 1 | ADR-0005 + 0012 |
| D | Distraction Blocker | `docs/modules/distraction-blocker/EXPANDED.md` | 1 | ADR-0011 |
| E | Site + Auth + Onboarding | `docs/modules/auth-and-site/EXPANDED.md` | 1 | ADR-0013 |
| W | Writing Space | `docs/modules/writing-space/EXPANDED.md` | 2 | (none yet — recommend ADR-0015 first) |
| L | Micro-Learning | `docs/modules/micro-learning/EXPANDED.md` | 2 | (none yet — recommend ADR-0016 + 0017 first) |
| B' | Brain Training | `docs/modules/brain-training/EXPANDED.md` | 2 | (none yet — recommend ADR-0018 + 0019 first) |

Lane F (Coordination) foundational work also done: agent-gateway
openapi vendored, weekly drift CI live, upstream issues
notbleaux/ZeSporteXte#117 (@njz/ui publish) and #118 (vaultbrain
extension) filed.

Each EXPANDED.md follows an identical 11-section template. A subagent
reading **just one** EXPANDED.md + `.agents/AGENT_CONTRACT.md` + the
source ADR(s) has everything needed to implement that lane.

## What you do in **this** session

**Pick exactly one lane and implement it.**

Per the plan's Option D-α (single lane per session, serial), each fresh
session gets the full budget for one lane. Phase D Wave 1 proved that
splitting budget across multiple subagents fails; one focused
implementation per session is the recoverable path.

### Recommended lane selection order

1. **Lane F continuous tasks first if any are due** (monthly cleanup,
   contracts drift triage). These are operational — check
   `.agents/active/upstream-coordination.md` for status.
2. **Phase-1 lanes by dependency order:**
   - **Lane E first** — it unblocks D's calendar OAuth. The E5 signal
     is the most-cited cross-lane hand-off.
   - **Lanes A / B / C in parallel** (different sessions) — they're
     fully independent.
   - **Lane D last in Phase 1** — depends on Lane E's E5 signal.
3. **Phase-2 lanes (W / L / B')** — gated on Phase-1 exit per
   `.agents/PHASE_GATES.md`. Don't start these until at least one
   Phase-1 lane is OPEN and Phase-1 MAU targets show traction.

### Per-lane strategy

1. **Branch:** `git checkout -b feat/<lane>-stage-3-impl-<short>`
   (e.g. `feat/a-focus-machine`, `feat/e-supabase-auth-shell`).
2. **Read these files (in order):**
   - `.agents/AGENT_CONTRACT.md` — what you can and cannot do.
   - `docs/modules/<lane>/EXPANDED.md` — the spec you implement.
   - The source ADR(s) named in §1 of the EXPANDED.md.
   - `packages/@njz-os/<package>/src/*.ts` — existing Phase-0 stubs
     you'll extend.
3. **ADR prerequisites** (Phase-2 only — Lane W, L, B' each have
   recommended new ADRs flagged in their §11):
   - **Lane W:** ADR-0015 (editor stack — Tiptap recommended) must land
     first.
   - **Lane L:** ADR-0016 (content licensing) + ADR-0017 (illustration
     hosting at scale) must land first.
   - **Lane B':** ADR-0018 (adaptive engine bounds) + ADR-0019
     (cognitive-profile baseline cohort) must land first.
   - Each ADR is a *separate small PR* before the implementation PR.
4. **Work through the Task list in the EXPANDED.md.** Each Task is
   one commit; subtasks are commit-shape work within. Universal
   success per task: `pnpm typecheck` + `lint` + `test` + `node
   tools/doc-tier-check/index.mjs` all green.
5. **Stop after each clean commit** if budget is thin. Better partial
   + clean than full + broken.
6. **Open PR** when the lane (or your achievable subset of tasks) is
   shipped. Title: `[<channel>] Lane <X> — <topic>`. Body should
   reference EXPANDED.md + source ADR + list completed tasks +
   note any deferred tasks.
7. **Do NOT flip the gate** in `.agents/PHASE_GATES.md` —
   orchestrator follow-up (per the A8 / B8 / C7 / D7 / E8 / W10 /
   L8 / B'10 pattern in every EXPANDED.md).

### What "implementation" specifically means

For each lane you'll add files to:

- `packages/@njz-os/<package>/src/` — domain logic, state machines,
  algorithms.
- `packages/adapters/<adapter>/src/` (only Lane E modifies the
  identity-client; others consume existing stubs).
- `apps/web/src/modules/<slug>/` — UI surface; replaces the
  `PhaseStub` route currently mounted.
- `tests/e2e/<lane>-*.spec.ts` — at least one end-to-end test per
  lane.
- `content/cards/`, `content/journey/`, `assets/sources/` —
  content/asset authoring for lanes that need it (L, B', C).

You may NOT:

- Touch `.agents/PHASE_GATES.md`.
- Modify existing ADRs 0001–0014.
- Cross channel boundaries (each EXPANDED.md §1 declares the channel
  + allowed paths; respect them).
- Bypass pre-commit hooks (`--no-verify`).

## Phase-1 exit criteria reminder

From `MASTER_PLAN.md`:

- [ ] All 5 Phase-1 `G1.*` gates OPEN in `.agents/PHASE_GATES.md`.
- [ ] `pnpm test:e2e` covers one full end-to-end smoke (focus session
      → decoration unlock → vaultbrain sync).
- [ ] Lighthouse perf + a11y + PWA ≥ 85 on `apps/web` main routes.
- [ ] DR-0002 (Phase 1 launch) authored and merged.
- [ ] `MASTER_PLAN.md` current-phase block advanced to Phase 2.

## After your session

Choose one:

- **Continue with another lane** (next session): same Option D-α.
- **Open the gate** for the lane you just implemented: orchestrator
  follow-up PR — flip `PHASE_GATES.md`, append `DECISION_LOG.md`,
  drop a logbook entry.
- **Phase-1 exit + Phase-2 transition:** when all 5 G1.* gates OPEN,
  author `docs/dev-reports/DR-0002-phase-1-launch.md`, advance
  `MASTER_PLAN.md`, open the final transition PR. Phase-2 lanes
  (W / L / B') then unblock.

## Failure modes — what to do

| Symptom | Action |
|---------|--------|
| Session budget exhausted mid-task | Commit the most recent clean work; push; open PR with what's done + a follow-up handoff |
| ADR prerequisite for Phase-2 lane not yet landed | Stop implementation; open the ADR first (separate small PR); resume after ADR Accepted |
| Cross-lane file touch needed | Surface to user via `AskUserQuestion`; do not expand scope |
| Universal success criterion red | Fix the root cause; do not bypass; if can't fix, open a `BLOCKED` follow-up handoff |
| Vaultbrain endpoints (per ADR-0008) not yet exposed upstream | Mock the adapter; queue events locally; flush on connection — every EXPANDED.md documents this fallback |
| Subagent prompt too long when spawned | Trim the required-reading; the EXPANDED.md is self-contained — only one file needs to be read per lane |

## What's durable on `main` right now

| Item | Status |
|------|--------|
| ADR-0001 .. ADR-0014 | All Accepted; on `main` |
| Prototype-system specs PS-001..007 | All on `main`; footers point at corresponding EXPANDED.md |
| 8 EXPANDED.md docs | All on `main` (after merge of `docs/stage-3-phase-2-module-expansions` branch this session opens) |
| Lane F foundational | On `main` (PR #21 merged); upstream issues filed; drift CI live |
| Plan + workplan | `/root/.claude/plans/plan-next-stages-to-concurrent-rocket.md` (ephemeral) + `.agents/session-workplans/SW-20260524-stage-3-lanes.md` (durable) |

## Quick-start commands

```bash
cd /home/user/satorXrotas
git checkout main
git pull origin main

# Pick your lane:
LANE=a        # or b, c, d, e, w, l, b'
git checkout -b feat/${LANE}-stage-3-impl-<short> main

# Read the spec:
cat docs/modules/<module>/EXPANDED.md

# Begin implementation per Task list inside the EXPANDED.md.
# Universal verification before each commit:
node tools/doc-tier-check/index.mjs
# (then per-package once code lands)
pnpm --filter @njz-os/<package> test --passWithNoTests
pnpm --filter @njz-os/<package> typecheck

# Open PR:
git push -u origin feat/${LANE}-stage-3-impl-<short>
# Then mcp__github__create_pull_request from the agent harness.
```

## Sign-off when you finish

1. Append `.agents/DECISION_LOG.md` per task completed (one line each).
2. Open the lane PR.
3. If your lane was a Phase-2 prerequisite (ADR-0015/16/17/18/19), the
   ADR PR comes first, then the implementation PR layered on top.
4. Drop a follow-up handoff if your work needs continuation in another
   session.

Good luck. Build it once, build it right.
