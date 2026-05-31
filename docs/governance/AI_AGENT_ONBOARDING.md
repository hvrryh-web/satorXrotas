[Ver001.000]

# AI Agent Onboarding — NJZ RAT-OS

> **Purpose:** a fresh agent should be able to read this single doc and
> be productive within 3 minutes. Optimised for context-budget
> efficiency: pointers over copies, the minimum set of decisions to
> recall.
> **Status:** active.
> **Authored:** 2026-05-30.

---

## 1. What you are working on (60 seconds)

NJZ RAT-OS is a **unified wellness-productivity OS** with seven modules
(Focus Hero, Soundscapes, Distraction Blocker, Writing Space,
Micro-Learning, Brain Training, PolyCo.World metaverse). Brand =
`NJZ RAT-OS`; technical namespace = `njz-os`; code scope = `@njz-os/*`.

The repo is a **pnpm + Turborepo monorepo** with:

- `apps/site` — Next.js 15 marketing site (SSG/ISR)
- `apps/web` — Vite + React 19 webapp (SPA, all modules)
- `packages/@njz-os/*` — domain packages (focus-engine, audio-engine,
  polyworld, ui, core, …)
- `packages/adapters/*` — typed HTTP/WS clients into upstream services
- `contracts/openapi/` — vendored contracts (Lane F territory)

Upstream platform: `notbleaux/ZeSporteXte`. Consume via `@njz/*` npm
scope + HTTP. Never push there from this repo without explicit user
authorization.

---

## 2. What's already built (30 seconds)

- All 14 ADRs (0001-0014) Accepted, on `main`.
- 8 EXPANDED.md docs (one per module).
- PR-25 portfolio uplift: 14/16 SHIPPED + 2/16 SCAFFOLDED.
- All 5 Phase-1 lanes (A, B, C, D, E) have working module surfaces.
- **149 unit tests across 10 packages**, all green on `main`.

For exact current state, read `.agents/handoff/session-*.md` (newest
first) and `docs/program-management/PR-25-portfolio-uplift.md` §G.1.

---

## 3. Mandatory reads (90 seconds)

In strict order:

1. `MASTER_PLAN.md` — current phase + scope.
2. `.agents/AGENT_CONTRACT.md` — hard rules + soft rules + domain boundaries.
3. `.agents/PHASE_GATES.md` — which features are unlocked.
4. **This doc** (you're reading it).
5. `docs/governance/TASK_FORMAT_CONVENTION.md` — task / evidence shape.
6. The latest `.agents/handoff/session-*.md` — pickup pointer.

If your task touches a specific module:

- Read `docs/modules/<module>/EXPANDED.md` — the implementation spec.
- Read the module's source ADR(s) named in §1 of that EXPANDED.md.

That's it. **Do not** load files outside this list until you need them.

---

## 4. Tool ladder (what to use, when)

| Goal | Tool |
|------|------|
| Read a known file | `Read` (preferred over `cat`) |
| Edit an existing file | `Edit` (preferred over `Write` for partial edits) |
| Find a symbol or string | `Bash` with `grep -rn` (preferred over `find`) |
| Open a PR | `mcp__github__create_pull_request` (no `gh` CLI in this env) |
| Merge a PR | `mcp__github__merge_pull_request` (squash merge, preserves PR title) |
| Run tests | `pnpm test` (full repo) or `pnpm --filter @njz-os/<pkg> test` |
| Validate docs | `node tools/doc-tier-check/index.mjs` |
| Validate bundle | `node tools/bundle-budget/check.mjs` (after `pnpm build`) |
| Rebuild tokens | `pnpm tokens:build` (and `pnpm tokens:check` for CI parity) |

---

## 5. Universal success criteria

Before every commit:

```bash
pnpm typecheck             # 28/28 tasks (or current count)
pnpm lint                  # 16/16 tasks
pnpm test                  # all suites green
node tools/doc-tier-check/index.mjs
```

If any red → fix, don't bypass. Pre-commit hooks enforce this anyway.

---

## 6. Commit + PR cadence

- Branch: `<type>/<short-description>` (e.g., `feat/lane-a-vaultbrain-wiring`).
- Commit per logical task (see `TASK_FORMAT_CONVENTION.md`).
- PR title: `[<channel>] <description>` matching `.agents/COORDINATION_PROTOCOL.md`.
- PR body: *Why* section + verification table + out-of-scope list +
  checklist matching `.agents/CODEOWNER_CHECKLIST.md`.
- Squash-merge via `mcp__github__merge_pull_request`.
- Delete the branch after merge; re-sync local `main`.

---

## 7. Hard rules (ABSOLUTE)

1. No pushes to `main`. Open a PR.
2. No deletes on `legacy/satire-deck-veritas`.
3. No new root `.md` files unless added to
   `.doc-tiers.json` → `manifest.approved_root_files`.
4. No new domain types without consulting `SCHEMA_REGISTRY.md` first.
5. No `--no-verify` to bypass hooks.
6. No backwards-compat shims during Phase 0 / 1.
7. No model identifier strings (e.g., `claude-opus-4-7`) in commits /
   PR bodies / code comments — chat-only.
8. Always log substantive decisions in `.agents/DECISION_LOG.md`.

---

## 8. When stuck

- **Unclear direction** → `AskUserQuestion` with 2-4 typed options.
- **Cross-channel touch needed** → split the PR; surface via the
  handoff.
- **Test failure on `main`** → bisect; open `fix/…` branch; do NOT
  start new lane work until clean.
- **ADR prerequisite missing** → open the ADR PR first; resume after
  Accepted.
- **Session budget thin** → commit the last clean unit; push; drop a
  follow-up handoff.

---

## 9. What good looks like

A well-shaped PR from this project:

- Body has *Why* + *What* + *Verification table* + *Out-of-scope* + checklist.
- Touches one channel (see `COORDINATION_PROTOCOL.md`).
- Adds tests proportional to surface introduced (see
  `PERFORMANCE_DEFINITIONS.md` §6).
- Ends with a one-line DECISION_LOG entry per substantive change.
- Mentions every dependency it consumes (PR-25 items, prior ADRs, sibling lanes).

Reference PRs to study (all merged on `main`):

- PR #32 (Lane A — Focus Engine) — clean pure-reducer + React hook pattern.
- PR #34 (Lane B — Audio Engine) — pure-math + AudioContext-bound factory split.
- PR #27 (PRX-25 consumer wave) — typed HTTP adapter with schema validation + retry + observability.
- PR #30 (Lane E auth shell) — provider-pattern abstraction for swappable backends.

---

## 10. Cross-references

- `MASTER_PLAN.md` — phase + scope.
- `.agents/AGENT_CONTRACT.md` — full behavioural contract.
- `.agents/COORDINATION_PROTOCOL.md` — channels + naming.
- `docs/governance/TASK_FORMAT_CONVENTION.md` — task / evidence shape.
- `docs/governance/PERFORMANCE_DEFINITIONS.md` — budgets + tests floor.
- `docs/governance/VERIFICATION_MATRIX_PROTOCOL.md` — DONE-claim audit trail.
- `docs/governance/LANE_CLOSURE_MANIFEST_TEMPLATE.md` — per-lane closure shape.
- `.agents/RISK_REGISTER.md` — deferred / out-of-scope items live there.

---

*Read once per fresh session. Updates require a DECISION_LOG entry.*
