[Ver001.000]

# Handoff — Stage 3 Documentation Sprint (Next Session)

**Date:** 2026-05-24
**Author:** claude-opus-4.7 (orchestrator)
**Status:** ready to pick up
**Audience:** the next agent session continuing the Stage 3 documentation sprint

---

## Where you are picking up

The current session completed **5 expanded module documents** for the
Phase-1 lanes (A–E):

| Lane | Module | EXPANDED.md path | Lines |
|------|--------|-------------------|-------|
| A | Focus Hero | `docs/modules/focus-hero/EXPANDED.md` | 629 |
| B | Soundscapes + Deep Canvas | `docs/modules/soundscapes/EXPANDED.md` | 630 |
| C | PolyCo.World + Asset Pipeline | `docs/modules/polyco-world/EXPANDED.md` | 615 |
| D | Distraction Blocker | `docs/modules/distraction-blocker/EXPANDED.md` | 475 |
| E | Site + Auth + Onboarding | `docs/modules/auth-and-site/EXPANDED.md` | 608 |

Each follows the same **11-section template** documented inside the
files. Each is self-contained — a fresh subagent reading one of these
+ AGENT_CONTRACT + the source ADR has everything needed to implement
that lane.

These five docs are on branch `docs/stage-3-module-expansions` and
landed (or will land) via the PR titled
`[architecture + docs] Stage 3 — ABCDE expanded module documentation`.

## What you do this session

**Author three more expanded module documents** for the Phase-2 modules
using the exact same 11-section template and depth target (500–900
lines per doc).

| Lane (future) | Module | New path | Source PS |
|---------------|--------|----------|-----------|
| (Phase-2 W) | Writing Space | `docs/modules/writing-space/EXPANDED.md` | PS-004 |
| (Phase-2 L) | Micro-Learning | `docs/modules/micro-learning/EXPANDED.md` | PS-005 |
| (Phase-2 B') | Brain Training | `docs/modules/brain-training/EXPANDED.md` | PS-006 |

### Strategy

1. **Branch:** `git checkout -b docs/stage-3-phase-2-module-expansions main`.
2. **Read the existing template first.** Open
   `docs/modules/focus-hero/EXPANDED.md` and skim its 11 sections —
   this is the canonical structure. Match it section-for-section.
3. **Read the source PS files** (PS-004, PS-005, PS-006) for the
   feature surface to expand.
4. **One commit per module** in lane order (W → L → B'). Each commit's
   message follows the template used in this branch's commits — see
   `git log --oneline docs/stage-3-module-expansions` for examples.
5. **Architectural gaps surface as ADR candidates.** None of PS-004,
   PS-005, PS-006 have dedicated ADRs yet (only PS-001..PS-007 are
   summarised in the Phase-1 ADR set, and only PS-001/2/3/7 map to
   Phase-1 ADRs). When your EXPANDED.md §11 surfaces a real
   architectural decision (e.g. editor stack for Writing Space, SM-2
   algorithm tuning for Micro-Learning, adaptive-difficulty engine for
   Brain Training), recommend a follow-up ADR number (ADR-0015 / 0016 /
   0017) and document the open question. Do NOT author the ADR in this
   session — it belongs to a later architecture pass.
6. **Update `.doc-tiers.json`** — `docs/modules/` is already T1 from
   the previous commit; no change needed.
7. **Update `.doc-registry.json`** — add the three new
   "implementation-ready" routes.
8. **Update `.agents/DECISION_LOG.md`** — one entry per doc authored.
9. **Add footer pointers** to PS-004/005/006 replacing the "deferred"
   placeholder this session left in their files.
10. **Push + open PR** titled
    `[architecture + docs] Stage 3 — Phase-2 module documentation (PS-004/005/006)`.

### 11-section template recap

Open `docs/modules/focus-hero/EXPANDED.md` for the canonical reference.
Sections (each must be present, depth varies by content):

1. Module identity & scope (status, owner role, channel, gates, ADRs, PS, parent docs, plan reference)
2. Architecture (ASCII diagram + component map + key trade-offs + impl extensions)
3. Domain types & contracts (TypeScript signatures, schema, vaultbrain endpoints called)
4. Implementation walkthrough — task by task (each lane Task → code-shape sketch + commit message)
5. Telemetry & analytics events (per `contracts/events/progression-events.json`)
6. Test plan (unit / integration / E2E / a11y / perf / cross-browser / cross-device)
7. Accessibility plan (per-component WCAG 2.2 AA checklist)
8. Risk register (likelihood × impact × mitigation)
9. Cross-lane handoffs (what this module consumes + emits)
10. Out of scope (deferred to later phases)
11. Open questions / TODOs (with recommended defaults + decision owners)

### Quality bar to maintain

- **Self-contained:** A subagent reading only this doc + AGENT_CONTRACT
  + the source PS + (where applicable) any later-authored ADR should be
  able to implement the module.
- **Honest about gaps:** PS-004/005/006 have no Phase-1 ADRs. Flag
  every architectural assumption you make in §11 with a recommended
  follow-up ADR ID and a decision owner.
- **Cross-link rigorously.** Every "See also" reference must resolve
  to an existing file. Run `node tools/doc-tier-check/index.mjs`
  before each commit.
- **Match the depth target.** 500–900 lines per doc. Going lower is
  acceptable for narrower modules; going higher only if the module
  surface genuinely warrants it.

## After your session (next-next session and beyond)

Once all eight expanded module docs exist (5 from this session + 3 from
yours), the **code-implementation phase** begins. Per the plan's Option
D-α (documented in
`.agents/handoff/phase-d-wave-1-aborted-20260524.md`):

- **One lane per session.** Each session spawns a single subagent (or
  the orchestrator works directly) on one of the 8 modules.
- **Required reading per session is trimmed.** With the EXPANDED.md
  docs in place, the subagent reads only:
  - `docs/modules/<lane>/EXPANDED.md`
  - `.agents/AGENT_CONTRACT.md`
  - The source ADR if a Phase-1 lane (A/B/C/D/E)
  - Source PS for Phase-2 lanes (W/L/B')
- **Branch naming:** `feat/<lane>-impl-<short>` (e.g.
  `feat/a-focus-machine`).
- **Wave-2 dependencies still apply:** Lane D Wave 2 waits on Lane E's
  E5 signal even at the code-implementation phase.
- **Lane E remains the most cross-cutting** — it should be implemented
  first or in parallel with A/B/C so the auth surface is available
  when D, W, L, B' need to consume it.

## Quick-start commands for this session

```bash
cd /home/user/satorXrotas
git checkout main
git pull origin main
git checkout -b docs/stage-3-phase-2-module-expansions main

# Read the canonical template:
cat docs/modules/focus-hero/EXPANDED.md | head -120

# Read the source PS files:
cat docs/prototype-systems/PS-004-writing-space.md
cat docs/prototype-systems/PS-005-micro-learning.md
cat docs/prototype-systems/PS-006-brain-training.md

# After authoring each EXPANDED.md, commit per-module:
git add docs/modules/writing-space/EXPANDED.md docs/prototype-systems/PS-004-writing-space.md
git commit -m "docs(modules): Writing Space (Phase-2 W) expanded module documentation"
# ... and so on for L, B'.

# Verification before push:
node tools/doc-tier-check/index.mjs
git push -u origin docs/stage-3-phase-2-module-expansions
```

Then open the PR via `mcp__github__create_pull_request`.

## What you must NOT do

- **No code changes** in `apps/*`, `packages/*`, `services/*` beyond
  references in the docs. Code implementation is for later sessions.
- **No new ADRs** in this session. Surface candidates in §11; defer
  authorship to a dedicated ADR sprint.
- **No `.agents/PHASE_GATES.md` edits.** Gate flips are orchestrator
  follow-up territory (per the same A8/B8/C7/D7/E8 pattern).
- **No modifications to existing ADRs (ADR-0001 through ADR-0014).**
  All are Accepted and immutable barring a supersession PR.
- **No changes to `docs/modules/focus-hero/EXPANDED.md` etc.** They
  shipped at the depth they shipped at; if you find a gap, flag it as
  a follow-up doc-fix issue rather than amending in this PR.

## Context you can rely on

The repo at `b380dde` (Phase C merge to main) carries:

- All Phase-0 + Phase-1 + Phase-2 ADRs (0001–0014, all Accepted).
- Full prototype-system specs PS-001..PS-007 (60–74 lines each — your
  source material).
- Stage 3 session workplan at
  `.agents/session-workplans/SW-20260524-stage-3-lanes.md` (six
  lanes documented; the Phase-2 modules are intentionally **not** in
  this workplan — they're future lanes you can sketch lightly).
- Upstream issues #117 (@njz/ui publish) and #118 (vaultbrain
  extension) filed and tracked in
  `.agents/active/upstream-coordination.md`.
- Vendored `contracts/openapi/agent-gateway.yaml` at pinned upstream
  SHA `22131186e5b179a73e90bbe98dacc85fb558765f`.
- Weekly drift CI at `.github/workflows/contracts-drift.yml`.

The plan-mode local file at
`/root/.claude/plans/plan-next-stages-to-concurrent-rocket.md` may or
may not survive into your session (it's ephemeral). Treat **this
handoff** + the in-repo session workplan as the durable source of truth
for what to do.

## Failure modes — what to do if you hit them

| Symptom | Action |
|---------|--------|
| Session-budget exhausted mid-doc | Stop after the most recent clean commit; push the partial branch; open a PR with what's done; leave a follow-up handoff in `.agents/handoff/` describing what remains |
| `pnpm typecheck`/`lint`/`test` red on a file you didn't touch | Surface to user via AskUserQuestion or a comment in the PR body. Don't try to fix unrelated regressions |
| `node tools/doc-tier-check/index.mjs` fails after your edits | Re-check `.doc-tiers.json` glob coverage; the new EXPANDED.md paths fall under `docs/modules/` which is already T1 |
| Cross-link in an EXPANDED.md points at a file that doesn't exist | Replace with a valid reference; never leave a dangling link |
| Source PS file is too thin to expand into a 500-line EXPANDED.md | Acceptable to ship a shorter doc (300+ lines) if the module surface is genuinely narrow. Note this in §11 |

## Sign-off

When you finish this session:

1. Append to `.agents/DECISION_LOG.md` (one line per doc authored).
2. Open the PR.
3. Drop a follow-up handoff at
   `.agents/handoff/stage-3-code-implementation-handoff.md` directing
   the *next-next* session toward code implementation per Option D-α.

Good luck.
