[Ver001.000]

# AGENT_CONTRACT — NJZ RAT-OS

This is the behavioural contract any AI agent operating in this repository must honour. Read it once per session and re-read it whenever the user changes scope.

## You Are Working In

`hvrryh-web/satorXrotas` — the NJZ RAT-OS monorepo. Consumer wellness-productivity OS. Two surfaces: marketing site (Next.js) and webapp (Vite + React). Shared packages under `packages/@njz-os/*`. Adapters to upstream platform under `packages/adapters/*`.

Upstream platform: `notbleaux/ZeSporteXte`. You can read it (via the `notbleaux/zesportexte` MCP tools) but you must not push changes there from this session unless explicitly asked.

## Hard Rules

1. **No pushes to `main`.** Open a PR. Even if a hook fails, do not bypass with `--no-verify`.
2. **No deletes on `legacy/satire-deck-veritas`.** That branch is the immutable archive of the pre-RAT-OS repo state.
3. **No new root-level `.md` files** unless added to `.doc-tiers.json` → `manifest.approved_root_files` in the same commit.
4. **No new domain types without consulting `.agents/SCHEMA_REGISTRY.md` first.** If the type exists upstream in `@njz/*`, import it. If it's RAT-OS-specific, define it in `@njz-os/core` and register it.
5. **No backwards-compatibility shims** during Phase 0/1. When an API changes, change all callers in the same commit.
6. **No dead code.** No `// removed`, no commented-out blocks, no orphan files.
7. **No comments explaining WHAT the code does.** Only WHY when it's non-obvious.
8. **Always log substantive decisions** in `.agents/DECISION_LOG.md` (one line each).
9. **Always check `.doc-tiers.json`** before loading any `.md` file. Do not load T2.
10. **Never invent service endpoints.** If an integration isn't in `contracts/openapi/njz-rat-os.yaml`, you need an ADR before adding one.

## Soft Rules (default behaviour; can be overridden by user)

- Prefer editing existing files over creating new ones.
- Prefer composition over inheritance, types over classes.
- Prefer TanStack Query over hand-rolled fetch wrappers.
- Prefer Zustand over Redux for UI state, XState for complex state machines.
- Prefer Tailwind utility classes over CSS modules; tokens come from `@njz-os/ui`.
- Prefer pixel-perfect to the design system over creativity.

## Domain Boundaries (Do Not Cross)

| Layer | Allowed imports |
|-------|-----------------|
| `apps/*` | Any package, any adapter, `@njz/*` from upstream |
| `packages/@njz-os/*` | Other `@njz-os/*`, `@njz/*` upstream types, std libs. **Never** import from `apps/` or `services/` |
| `packages/adapters/*` | `@njz-os/core`, network libs, `@njz/*` SDK. **Never** import other `@njz-os/*` packages |
| `services/*` | Anything server-side. **Never** import from `apps/` |
| `contracts/*` | Pure schema. No code. |

CI enforces these via `eslint-plugin-boundaries`.

## When You're Unsure

1. Re-read `MASTER_PLAN.md` — is your task in scope for the current phase?
2. Check `.agents/PHASE_GATES.md` — is the feature unlocked?
3. Search `docs/architecture/ADR/` — has this been decided?
4. Search `.agents/DECISION_LOG.md` — has this been logged?
5. If still unsure, ask the user. Do not guess.

## Common Anti-Patterns We've Seen

- Adding a "v2" file alongside a "v1" without removing v1. (Just edit v1.)
- Copy-pasting `@njz/*` upstream code into `packages/`. (Use the package; don't fork.)
- Writing a service in `services/` that duplicates one in ZeSporteXte. (Use an adapter.)
- Adding TODO comments without a tracking issue. (Don't.)
- Bypassing pre-commit with `--no-verify`. (Don't.)
- Claiming "DONE" without an evidence anchor. (Every closed task references PR # + SHA + tests, per `docs/governance/VERIFICATION_MATRIX_PROTOCOL.md`.)
- Inventing a task ID outside the `<LANE>-<PHASE>-<NN>` convention. (Per `docs/governance/TASK_FORMAT_CONVENTION.md`.)
- Treating an "out of scope" item as forgettable. (Every out-of-scope item gets a row in `.agents/RISK_REGISTER.md`.)

## Governance Surface (Phase 1)

Every agent reads these on first invocation of a session:

1. `MASTER_PLAN.md` — current phase + scope.
2. This file (`AGENT_CONTRACT.md`) — behavioural contract.
3. `.agents/PHASE_GATES.md` — which gates are open / unlock-pending.
4. `.agents/SCHEMA_REGISTRY.md` — canonical types.
5. `docs/governance/AI_AGENT_ONBOARDING.md` — 3-minute fast-start (added 2026-05-30).
6. `docs/governance/TASK_FORMAT_CONVENTION.md` — task IDs + status + evidence shape.
7. The latest `.agents/handoff/session-*.md` — pickup pointer.

Reference when needed:

- `docs/governance/PERFORMANCE_DEFINITIONS.md` — concrete budgets + test floors.
- `docs/governance/VERIFICATION_MATRIX_PROTOCOL.md` — how DONE-claims map to evidence.
- `docs/governance/LANE_CLOSURE_MANIFEST_TEMPLATE.md` — per-lane closure shape.
- `.agents/RISK_REGISTER.md` — active deferred / out-of-scope rows.

## End of Session

Before you close a session:

1. Append one line to `.agents/DECISION_LOG.md` if you made a decision.
2. If you completed a substantive piece of work, drop a session workplan in `.agents/session-workplans/` describing what you did and what's next.
3. If you opened a PR, link the PR number from `.agents/active/`.
