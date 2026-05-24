[Ver001.000]

# ADR-0001 — Monorepo Structure & Brand Naming

- **Status:** Accepted
- **Date:** 2026-05-24
- **Deciders:** @hvrryh-web
- **Tags:** monorepo, naming, structure

## Context

`hvrryh-web/satorXrotas` was previously an in-flight "Satire-deck-Veritas" restructure (eSports analytics framework, mid-migration). The new purpose is the **NJZ RAT-OS** consumer wellness-productivity OS — a different product, sibling to the eSports work in `notbleaux/ZeSporteXte`.

We need a structure that:

- Hosts a marketing site and a webapp (distinct runtimes).
- Hosts shared domain packages (`@njz-os/*`).
- Hosts thin adapter packages bridging to ZeSporteXte's services.
- Mirrors the upstream `notbleaux/ZeSporteXte` framework (NJZPOF v0.2) for agent portability.
- Preserves prior content losslessly.

## Decision

1. **Brand:** `NJZ RAT-OS` (marketing) / `NJZ-OS` (technical). Repo name kept as `satorXrotas`.
2. **Monorepo tooling:** pnpm workspaces + Turborepo. Matches upstream conventions exactly.
3. **Layout:** `apps/`, `packages/@njz-os/*`, `packages/adapters/*`, `packages/config/*`, `services/`, `contracts/`, `infra/`, `docs/`, `.agents/`, `ROOT_AXIOMS/`.
4. **Preservation:** prior contents preserved on `legacy/satire-deck-veritas` branch before wiping main.

## Consequences

**Positive:**

- Single brand identity (`NJZ RAT-OS`) consistent across marketing.
- Code namespace (`njz-os`, `@njz-os`) avoids collision with upstream `@njz/*`.
- Monorepo allows shared types and design tokens across surfaces without npm publish cycles.
- Adopting upstream tooling means agents can move between repos with minimal context switch.

**Negative:**

- Confusing for newcomers: brand vs technical name diverge. Mitigation: `STD-02 naming standards` + `CLAUDE.md` cover this explicitly.
- Two monorepos to keep in sync convention-wise. Mitigation: monthly cleanup protocol.

**Neutral:**

- Repo name `satorXrotas` is a legacy artifact. Renaming is out of scope and not worth the URL churn.

## Alternatives Considered

- **Polyrepo (separate site + webapp + adapters repos).** Rejected: shared types and design tokens become painful; release coordination overhead high.
- **Folder inside ZeSporteXte.** Rejected: different product, different deploy cadence, different team boundaries. Forces unrelated CI to run.
- **Lerna or Nx for orchestration.** Rejected: Turbo is what upstream uses; consistency wins.
- **Brand = NJZ-OS only (drop "RAT-OS").** Rejected: user explicitly chose the stylization for the brand surface.

## Related

- ADR-0002 (`@njz/*` consumption model)
- ADR-0004 (apps/site vs apps/web split)
- `ROOT_AXIOMS/02_STANDARDS/02-naming-standards.md`
