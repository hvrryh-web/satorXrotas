[Ver001.000]

# Handoff — Phase D Wave 1 aborted (session limits)

**Date:** 2026-05-24
**Author:** claude-opus-4.7 (orchestrator)
**Status:** pending fresh-session retry
**Affected:** Lanes A, B, C, E (Wave 1 of Phase D per the next-stages plan)

## What happened

Four concurrent `Agent`-tool subagents were launched per the Stage 3
execution plan:

| Lane | Agent ID | Duration | Total tokens | Tool uses | Outcome |
|------|----------|----------|--------------|-----------|---------|
| A — focus-engine | ab3624412732b1c12 | 102 s | 1,848 | 32 | session limit |
| B — audio-engine | a62235dc2ad0bb55e | 81 s | 1,514 | 26 | session limit |
| C — polyworld + assets | a39f0f6f8d8e4339e | 71 s | 1,337 | 24 | session limit |
| E — site + auth + onboarding | a1d65a48c37765300 | 40 s | 692 | 14 | session limit |

Each completed with the message **"You've hit your session limit · resets
11:30pm (UTC)"**. No real implementation work happened — token counts and
durations are consistent with "agent spent its budget reading required
files, then ran out". Zero commits produced on any of the four branches.

The harness asked each subagent to read 6–8 files before any edits
(ADRs, prototype-system spec, AGENT_CONTRACT, COORDINATION_PROTOCOL,
SCHEMA_REGISTRY, source stubs, workplan). That was already enough to
exhaust the per-subagent token budget against a shared, throttled session
pool.

## Cleanup performed

- Four `feat/{a,b,c,e}-stage-3` branches deleted (they pointed at
  `main`'s tip with no advance).
- Empty `.claude/worktrees/` directory removed (worktrees self-pruned on
  agent termination).
- Main worktree switched back to `main`.
- `.claude/` added to `.gitignore` so future worktree experiments cannot
  leave the repo with untracked state (the stop-hook caught this and was
  correct to complain).

## Diagnosis

The concurrent-Agent approach for Stage 3 has two stacked issues:

1. **Shared session budget.** Per-subagent token limits are reportedly
   independent, but in practice the four parallel agents drew from a
   single pool that was already partway depleted by the orchestrator
   conversation. Each got an unworkable slice.
2. **Required-reading overhead.** The harness expected each agent to
   load 6–8 files before any code. That's >2 K tokens per agent just in
   read calls before they can do useful work.

## Recommended next-session approach

When the session resets (≥23:30 UTC), retry Phase D with **one** of these
strategies — listed in order of preference:

### Option D-α — Serial, one lane per session

- Skip concurrency entirely. Each session spawns **one** lane subagent
  with a fresh budget; the orchestrator reviews on completion; then the
  next session spawns the next lane.
- 5 sessions for A → B → C → E → D in plan order (E first if Lane D is
  needed early via the E5 unblock signal).
- Pro: maximum budget per lane. Con: 5 sessions to clear Wave 1+2.

### Option D-β — Smaller scope per agent

- Re-issue the harnesses with only 2–3 tasks per agent instead of 7–8.
- Reduces the work each subagent commits to and the orchestrator can
  chain follow-up agents for remaining tasks.
- Pro: more agents finish within budget. Con: more orchestrator overhead.

### Option D-γ — Orchestrator-direct serial execution

- Orchestrator does the lane work itself, one Task at a time, with
  fresh sessions as needed. No subagent indirection.
- Maximizes session budget but loses parallelism entirely.
- Pro: predictable. Con: no concurrency.

### Option D-δ — Hybrid

- Orchestrator does Lane F continuous work + one feature lane per
  session via direct implementation; spawns *one* small subagent for the
  next-most-isolated lane in parallel.

**Recommendation:** start with **D-α** — single-lane per session in
serial. The plan's "fallback" branch already names this; we just hit it
sooner than expected. Lane A first (purely additive, smallest scope).

## What's still durable on `main`

Nothing was lost. Phase A + B + C all merged to `main` via PR #21:

- `b380dde` — Phase C / Lane F foundational
- DECISION_LOG appended with the F1–F4 narrative and now this Phase D
  abort entry.
- Upstream issues filed: notbleaux/ZeSporteXte#117 (@njz/ui) and #118
  (vaultbrain extension); their cadence is independent of this abort.

## What to do when picking this up

1. Open `/root/.claude/plans/plan-next-stages-to-concurrent-rocket.md`
   to re-orient on the lane harnesses.
2. Open `.agents/session-workplans/SW-20260524-stage-3-lanes.md` for the
   durable lane-task snapshot.
3. Read this handoff to understand why a single concurrent attempt
   already used the lane branches' name slots — recreate them in the
   fresh session (`git checkout -b feat/a-stage-3 main`, etc.).
4. Pick Option D-α (recommended) and spawn one lane subagent. Keep its
   required-reading list minimal — let it read what it needs as it
   needs it rather than front-loading.
