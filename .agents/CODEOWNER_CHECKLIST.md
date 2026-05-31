[Ver001.000]

# CODEOWNER_CHECKLIST — NJZ RAT-OS

What CODEOWNERS check before approving a PR. Live document; updates require an ADR if the checklist itself changes.

## Universal Checks (all PRs)

- [ ] PR title is `[<channel>] <description>` matching a channel in `.agents/COORDINATION_PROTOCOL.md`.
- [ ] PR body has a *Why* section, not just a *What*.
- [ ] All CI checks pass.
- [ ] Pre-commit hooks were not bypassed (`--no-verify` is grounds for request-changes).
- [ ] No new root-level `.md` files unless added to `.doc-tiers.json` → `manifest.approved_root_files` in the same PR.
- [ ] No comments explaining WHAT the code does (well-named identifiers should suffice). WHY comments are fine.
- [ ] No TODOs without a linked issue.
- [ ] No commented-out code.
- [ ] No backwards-compat shims unless explicitly noted as bridging an in-flight migration.

## Phase 1 Checks (current phase as of 2026-05-30)

- [ ] If touching `.agents/`, `.doc-tiers.json`, or `ROOT_AXIOMS/` → assigned to Coordinator role.
- [ ] If adding a new package → ADR exists for its scope + listed in `pnpm-workspace.yaml`.
- [ ] If editing PRD/OKRs → version header bumped, change reflected in `docs/dev-reports/`.
- [ ] If touching a lane (A/B/C/D/E) → lane closure manifest at `docs/program-management/LANE_<X>_MANIFEST.md` refreshed in the same PR (or row added on first touch).
- [ ] If introducing a new task → ID follows `<LANE>-<PHASE>-<NN>` per `docs/governance/TASK_FORMAT_CONVENTION.md`.
- [ ] If claiming `SHIPPED` on a task → evidence record present per `docs/governance/VERIFICATION_MATRIX_PROTOCOL.md` §2.
- [ ] If introducing an "out of scope" follow-up → row appended to `.agents/RISK_REGISTER.md`.
- [ ] If consuming a PR-25 uplift item → cited explicitly in the PR body and in the lane closure manifest.
- [ ] If a gate's unlock criteria are met → CODEOWNER opens a follow-up PR to flip `.agents/PHASE_GATES.md` (NOT in the implementation PR).
- [ ] If touching CI/budgets/runbooks → cross-checked against `docs/governance/PERFORMANCE_DEFINITIONS.md`.

## Architecture PRs

- [ ] ADR exists for the decision.
- [ ] `Status: Accepted` only when this PR is reviewed by ≥1 CODEOWNER.
- [ ] Schema changes propagated to `.agents/SCHEMA_REGISTRY.md`.

## Adapter / Contract PRs

- [ ] Upstream endpoint exists in `notbleaux/ZeSporteXte` (link in PR body).
- [ ] `contracts/openapi/njz-rat-os.yaml` updated.
- [ ] Generated client committed (`packages/adapters/api-client/src/generated/`).
- [ ] Smoke test against staging if Phase 0 exited.

## App / Module PRs (Phase 1+)

- [ ] Corresponding `PHASE_GATE` is `OPEN`.
- [ ] Tests added: unit + at least one integration.
- [ ] Accessibility check: keyboard navigation + ARIA roles + colour contrast.
- [ ] No imports from `apps/*` inside `packages/*`.
- [ ] No imports from `packages/@njz-os/*` inside `packages/adapters/*`.

## Infra PRs

- [ ] No production credentials in diff (detect-secrets pass).
- [ ] Rollback documented in PR body.
- [ ] Affected environments listed.

## Documentation PRs

- [ ] `[Ver]` header bumped if substantive.
- [ ] Cross-links between affected docs updated.
- [ ] If a routing answer changed, `.doc-registry.json` updated.

## After Approval

- [ ] Squash-merge if commit history is messy; merge-commit if every commit is meaningful.
- [ ] If decision was substantive, agent appends to `.agents/DECISION_LOG.md`.
- [ ] If PR closed a phase gate, `PHASE_GATES.md` updated in a follow-up PR.

## Reviewers Per Channel

(Resolved by `.github/CODEOWNERS` — this section is the human-readable mirror.)

| Channel | Primary reviewer role | Backup |
|---------|----------------------|--------|
| `framework` | Coordinator | Architect |
| `product-docs` | Architect | Coordinator |
| `architecture` | Architect | Critic |
| `web-app` | Implementer | Designer |
| `site` | Implementer | Designer |
| `packages-ui` | Designer | Implementer |
| `packages-engines` | Implementer | Architect |
| `adapters` | Data Engineer | Architect |
| `infra` | Platform | Critic |
| `tests` | Critic | Implementer |
| `dev-reports` | Coordinator | Architect |
