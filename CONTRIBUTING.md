# Contributing — NJZ RAT-OS

Thanks for contributing. A few non-obvious rules first; the rest is standard.

## Before You Start

1. Read `CLAUDE.md` (or `AGENTS.md` if you're a non-Claude tool) — agent contract + naming.
2. Read `MASTER_PLAN.md` — which phase are we in and what's locked.
3. Check `.agents/PHASE_GATES.md` — is the work you want to do currently unlocked?
4. Check `.doc-tiers.json` — load only T0 by default; T1 on demand; never T2.

## Branching

- `main` is protected. PRs only.
- Feature branches: `feat/<area>-<short-name>` (e.g. `feat/web-focus-hero-shell`).
- Agent branches: `claude/<topic>` or `<tool>/<topic>`.
- The legacy archive of the pre-RAT-OS repo lives on `legacy/satire-deck-veritas` — **do not delete or rebase it.**

## Commits

Conventional Commits format:

```
<type>(<scope>): <description>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `infra`, `ai`.

Common scopes: `site`, `web`, `ui`, `audio`, `focus`, `polyworld`, `adapters`, `agents`, `axioms`, `docs`, `infra`, `ci`.

## Code Style

- TypeScript strict mode is on. Unused locals/parameters fail the build.
- Format with Prettier (`pnpm format`). Lint with ESLint (`pnpm lint`).
- Comments: write none by default. Only when the *why* is non-obvious.
- No dead code, no commented-out blocks, no TODOs without an issue number.

## Adding a New Module Package

```bash
pnpm module:new <package-name>
```

Then:

1. Document it in `docs/prototype-systems/PS-XXX-<name>.md` (use the template).
2. Add it to `packages/@njz-os/<name>/README.md`.
3. Update `.agents/SCHEMA_REGISTRY.md` if you're introducing new domain types.

## Adding an ADR

```bash
pnpm adr:new "Short title here"
```

Then fill out the template in `docs/architecture/ADR/ADR-XXXX-<slug>.md`. Status starts at `Proposed`; flip to `Accepted` only after a reviewer approves the PR.

## Pre-commit Hooks

Husky + lint-staged runs:

- Prettier on staged files
- ESLint on staged `.ts/.tsx`
- `pnpm doc-tier:check`
- Detect-secrets baseline check

Do not bypass with `--no-verify`. If a hook fails, fix the cause.

## Pull Requests

- Open against `main`.
- Include a *Why* section (not just *What*).
- Link the relevant ADR or Prototype System spec when applicable.
- Tag at least one CODEOWNER (see `.agents/CODEOWNER_CHECKLIST.md`).
- All CI checks must pass before merge.

## Bigger Changes — Multi-Session Workplans

For anything spanning multiple sessions, drop a workplan in `.agents/session-workplans/SW-YYYYMMDD-<slug>.md` so the next agent can pick up where you left off. Cross-link it from `.agents/active/`.

## Reporting Bugs / Asking Questions

- GitHub Issues for bugs and feature requests.
- `SUPPORT.md` for usage questions.
- `SECURITY.md` for vulnerabilities (do not file public issues).
