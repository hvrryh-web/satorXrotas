# SATOR Branch Strategy

## Overview

The SATOR monorepo uses a structured Git branching model to ensure that:
- `main` always represents a working, deployable state
- Firewall enforcement is validated before any merge to `main`
- Features are developed and reviewed in isolation

---

## Branch Hierarchy

```
main (production)
  │
  └─ develop (integration)
        │
        ├─ feature/stats-schema-types
        ├─ feature/firewall-implementation
        ├─ feature/sator-web-ui
        └─ feature/api-endpoints
```

---

## Branch Definitions

### `main` — Production

| Property | Value |
|----------|-------|
| **Purpose** | Production-ready code only |
| **Merge from** | `develop` (via PR) |
| **Direct push** | ❌ Never |
| **Required checks** | All CI, firewall tests, schema validation |
| **Protected** | ✅ Yes |

Rules:
- All CI workflows must pass (`ci.yml`, `test-firewall.yml`, `validate-sator-schema.yml`)
- PR requires approval from `@hvrryh-web` (see `.github/CODEOWNERS`)
- Firewall policy (`docs/FIREWALL_POLICY.md`) must not be weakened without explicit review
- Merge strategy: **Squash and merge** to keep history clean

### `develop` — Integration

| Property | Value |
|----------|-------|
| **Purpose** | Integration branch; completed features merge here before `main` |
| **Merge from** | `feature/*` branches (via PR) |
| **Direct push** | ❌ Never (except emergency hotfix) |
| **Required checks** | All CI workflows |
| **Protected** | ✅ Yes |

Rules:
- Feature PRs must target `develop`, not `main`
- All automated tests must pass before merge
- Code review required for changes to `packages/` or `.github/workflows/`

### `feature/*` — Feature Branches

| Property | Value |
|----------|-------|
| **Purpose** | Isolated development of a single feature or fix |
| **Branch from** | `develop` |
| **Merge into** | `develop` |
| **Direct push** | ✅ Yes (by author) |
| **Required checks** | None (but CI runs) |

Naming convention:

```
feature/<short-description>        # New feature
fix/<short-description>            # Bug fix
chore/<short-description>          # Non-functional change
docs/<short-description>           # Documentation only
```

Examples:
- `feature/stats-schema-types`
- `feature/firewall-middleware`
- `fix/sanitize-recursive-objects`
- `docs/update-firewall-policy`

---

## Merge Requirements

### Merging `feature/*` → `develop`

- [ ] CI passes (`ci.yml`)
- [ ] TypeScript typechecks pass (if package files changed)
- [ ] At least one approving review (optional for solo development)
- [ ] PR description explains what changed and why
- [ ] No `GAME_ONLY_FIELDS` added to `packages/stats-schema`

### Merging `develop` → `main`

- [ ] All CI workflows pass (`ci.yml`, `test-firewall.yml`, `validate-sator-schema.yml`)
- [ ] Approving review from `@hvrryh-web`
- [ ] Firewall tests (`npm run test:firewall`) pass locally
- [ ] Schema validation (`npm run validate:schema`) passes
- [ ] No regression in determinism tests (Godot)
- [ ] `docs/FIREWALL_POLICY.md` is up to date
- [ ] `CONTRIBUTING.md` reflects any new workflow changes

---

## CI/CD Relationship

Each branch has automated workflows:

| Branch | Workflows |
|--------|-----------|
| Any PR to `main` | `ci.yml` + `test-firewall.yml` + `validate-sator-schema.yml` |
| Any PR to `develop` | `ci.yml` + `validate-sator-schema.yml` |
| Push to `main` or `develop` | `ci.yml` |

Workflows are defined in `.github/workflows/`. See those files for exact trigger
conditions.

---

## Emergency Hotfixes

For critical production fixes:
1. Branch from `main`: `git checkout -b fix/critical-description main`
2. Apply minimal fix
3. Open PR directly to `main` (requires `@hvrryh-web` approval)
4. After merge to `main`, also merge or cherry-pick into `develop`

---

*See also: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) · [FIREWALL_POLICY.md](FIREWALL_POLICY.md) · [CONTRIBUTING.md](../CONTRIBUTING.md)*
