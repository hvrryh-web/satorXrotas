[Ver001.000]

# CLAUDE.md — NJZ RAT-OS

This file orients Claude Code (and any agent powered by Claude / Sonnet / Opus / Haiku) when working in this repository.

## Project Overview

**NJZ RAT-OS** (brand) / **NJZ-OS** (technical) — a unified wellness-productivity OS combining seven modules (Focus Hero, Soundscapes, Distraction Blocker, Writing Space, Micro-Learning, Brain Training, PolyCo.World metaverse) into one cohesive web + webapp experience.

This repository is the **RAT-OS monorepo** (marketing site + webapp). It consumes shared services and packages from the upstream NJZ platform monorepo at `notbleaux/ZeSporteXte` via the `@njz/*` npm scope.

## Session Start Protocol — Run This Order

1. Read `MASTER_PLAN.md` — current phase, scope, success criteria.
2. Read `.agents/AGENT_CONTRACT.md` — behavioral contract.
3. Read `.agents/PHASE_GATES.md` — which features/phases are unlocked.
4. Read `.agents/SCHEMA_REGISTRY.md` — canonical types (check before defining new).
5. Consult `.doc-tiers.json` before loading any other `.md` (T0=always, T1=on-request, T2=never).

## Naming Conventions

| Surface | Use |
|---------|-----|
| Marketing, copy, README headlines | `NJZ RAT-OS` |
| Code, package names, paths, schemas | `njz-os`, `@njz-os/*` |
| Shared cross-product packages | `@njz/*` (defined upstream in ZeSporteXte) |
| Network namespace | `njz-os.{net,app,com}` (TBD by Ops) |

## Architecture Summary

```
Marketing site (apps/site, Next.js 15, SSG/ISR)
            │
            ▼
       Webapp (apps/web, Vite + React 19)
            │
            ├── @njz-os/* (local packages: ui, focus-engine, audio-engine, polyworld, …)
            └── adapters/* (typed HTTP/WS clients into ZeSporteXte services)
                       │
                       ▼
                ZeSporteXte:
                  services/vaultbrain    (persistent state + AI memory)
                  services/agent-gateway (MCP + agent routing)
                  services/api           (REST data plane)
```

## Commands

### Root

```bash
pnpm install              # Install workspace deps
pnpm dev:site             # Marketing site (Next.js)
pnpm dev:web              # Webapp (Vite)
pnpm build                # Turborepo: build all
pnpm lint                 # Lint all packages
pnpm typecheck            # tsc across all workspaces
pnpm test                 # Test all
pnpm doc-tier:check       # Validate .doc-tiers.json + manifest
pnpm adr:new "<title>"    # Scaffold new ADR
pnpm module:new "<name>"  # Scaffold a new @njz-os/* package
```

### Per-app

```bash
pnpm --filter @njz-os/site dev
pnpm --filter @njz-os/web dev
pnpm --filter @njz-os/web test
```

## Coding Standards

- **TypeScript strict** — `noUnusedLocals`, `noUnusedParameters` enabled. Unused vars fail typecheck.
- **Module boundaries** — apps consume packages; packages do NOT import from apps.
- **No backwards-compat shims** — when an API changes, change all callers in the same commit.
- **No speculative abstractions** — three similar lines is better than a premature factory.
- **Comments** — write none by default. Only when WHY is non-obvious (hidden constraint, subtle invariant, workaround for a specific bug).

## Commit Conventions

```
<type>(<scope>): <description>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `infra`, `ai`

Scopes by area: `site`, `web`, `ui`, `audio`, `focus`, `polyworld`, `adapters`, `agents`, `axioms`, `docs`, `infra`, `ci`.

Examples:
```
feat(focus): add 25/5 pomodoro state machine
docs(axioms): record principle PR-007 on offline-first
ai(agents): refresh PHASE_GATES after Phase 0 close
```

## Document Versioning

All canonical docs carry a version header at the top:

```
[VerMMM.mmm]
# Document Title
```

Increment `MMM` for breaking changes, `mmm` for additive/clarifying edits.

## Pre-commit Behavior

Pre-commit hooks will run lint, typecheck, and doc-tier validation. They will fail on:

- TypeScript errors
- ESLint errors (warnings allowed)
- Untracked root-level `.md` files not in `.doc-tiers.json` → `manifest.approved_root_files`
- Files > 1 MB

If a hook fails, fix the root cause. Never bypass with `--no-verify` unless explicitly asked.

## Multi-Agent Coordination

This repo follows **NJZPOF v0.2** (same framework as ZeSporteXte). The contract is in `.agents/AGENT_CONTRACT.md`. Read it before doing anything substantive.

Channels:

- `active/` — current sprint work
- `handoff/` — session-to-session passes
- `session/` — per-session workplans
- `phase-logbooks/` — historical phase notes
- `registry/` — agent registry

When you complete a substantive change, log a one-line entry in `.agents/DECISION_LOG.md` with the date, decision, and rationale.
