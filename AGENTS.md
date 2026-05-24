[Ver001.000]

# AGENTS.md — NJZ RAT-OS

This file is the entrypoint for any non-Claude agent (Codex, Cursor, Aider, Kimi, Zencoder, etc.) working in this repository. It mirrors `CLAUDE.md` in essence; tool-specific quirks belong in `.agents/skills/<tool>.md`.

## Read These, In Order

1. `MASTER_PLAN.md`
2. `.agents/AGENT_CONTRACT.md`
3. `.agents/PHASE_GATES.md`
4. `.agents/SCHEMA_REGISTRY.md`
5. `.doc-tiers.json` (consult before loading any other `.md`)

## What This Repo Is

`NJZ RAT-OS` — monorepo for the consumer wellness-productivity platform. Marketing site (`apps/site`) + webapp (`apps/web`) + shared packages (`packages/@njz-os/*`) + thin adapter layer (`packages/adapters/*`) that talks HTTP/WS to services hosted in `notbleaux/ZeSporteXte`.

## What This Repo Is Not

- Not a place for ZeSporteXte's `services/*` code. Add a typed adapter in `packages/adapters/` and call the service over the network instead.
- Not a place for the eSports platform code. That stays in `apps/web/src/hub-*/` of ZeSporteXte.
- Not a place for half-finished experiments. Use a `claude/...` branch.

## Hard Rules

- Never push to `main` directly. Open a PR from a feature branch.
- Never delete content from `legacy/satire-deck-veritas` — that branch is the historical archive of the previous repo iteration.
- Never edit `ROOT_AXIOMS/` files without recording the change in `.agents/DECISION_LOG.md`.
- Never bump a `[VerMMM.mmm]` major without an ADR.
- Never disable a pre-commit hook with `--no-verify`.

## Common Tasks

| Task | Where to start |
|------|----------------|
| Add a new module | `tools/module-new/` template; then update `docs/prototype-systems/` |
| Make a design decision | Scaffold ADR via `pnpm adr:new`; record in `docs/architecture/ADR/` |
| Document session outcome | Append to `.agents/DECISION_LOG.md` + drop a workplan in `.agents/session-workplans/` |
| Update product spec | Edit `docs/product/PRD.md`; bump version header |
| Add a service contract | Update `contracts/openapi/njz-rat-os.yaml` and regenerate `packages/adapters/api-client` |

## Skills Per Agent

Agent-specific guidance lives in `.agents/skills/<agent>.md` (e.g., `.agents/skills/codex.md`). If your tool has quirks (path handling, auth flow, sandbox limits), add a skill file rather than splaying special cases through main docs.
