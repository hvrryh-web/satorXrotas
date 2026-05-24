[Ver001.000]

# ADR-0002 — Consume `@njz/*` Packages From Upstream

- **Status:** Accepted
- **Date:** 2026-05-24
- **Deciders:** @hvrryh-web
- **Tags:** integration, packages, npm

## Context

RAT-OS needs design primitives, vaultbrain event types, agent-protocol types, and (later) auth types that already exist (or will exist) in `notbleaux/ZeSporteXte` under the `@njz/*` npm scope. Three integration models were on the table.

## Decision

Consume `@njz/*` packages via the npm registry with a versioned dependency. Wrap any upstream service calls in adapter packages (`packages/adapters/*`). No git submodule. No code copy.

Locally, developers may use `pnpm` `overrides` to point a `@njz/*` package at a sibling working copy of ZeSporteXte for fast iteration — but this is a dev convenience, not a CI mode.

## Consequences

**Positive:**

- Loose coupling: upstream can release independently; we bump when we want.
- Type safety end-to-end (TypeScript types come from `@njz/*`).
- Single point of change when upstream service interfaces evolve (the adapter layer).
- Easy to test in isolation: mock adapters with `msw`.

**Negative:**

- Versioning discipline required: locked-down pinning, periodic bump reviews.
- We pay the cost of an extra abstraction layer (the adapters) — but this pays back in testability and isolation.

**Neutral:**

- We don't own upstream release cadence. If `@njz/ui` ships a breaking change, we absorb it on our schedule.

## Alternatives Considered

- **Git submodule** of ZeSporteXte inside RAT-OS (e.g. `vendor/zesportexte`). Rejected: friction with two-way changes, awkward CI, conflates "our code" with "upstream code".
- **Copy/fork** the relevant ZeSporteXte services and packages. Rejected: divergence inevitable, defeats the shared-platform thesis, doubles maintenance.
- **Document only.** Define interfaces in docs without code-level consumption. Rejected: defers real integration risk.

## Related

- ADR-0003 (Vaultbrain as state backend)
- `docs/architecture/INTEGRATION_WITH_ZESPORTEXTE.md`
- `ROOT_AXIOMS/03_PROCEDURES/03-add-an-adapter.md`
