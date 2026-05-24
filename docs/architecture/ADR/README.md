# Architecture Decision Records (ADR)

Records of significant architecture decisions, with rationale and consequences. Format inspired by Michael Nygard.

## Filename Convention

`ADR-XXXX-<kebab-slug>.md`. Four-digit zero-padded. Monotonic.

## Template

See `docs/governance/ADR_TEMPLATE.md`.

## Status Values

- `Proposed` — in PR, not yet approved.
- `Accepted` — merged; in effect.
- `Deprecated` — no longer current; superseded by another ADR (link in header).
- `Superseded by ADR-NNNN` — replaced; keep file for historical record.

## Index (Bootstrap)

| ID | Title | Status |
|----|-------|--------|
| 0001 | Monorepo structure & brand naming | Accepted |
| 0002 | Consume `@njz/*` packages from upstream (no submodule, no fork) | Accepted |
| 0003 | Vaultbrain as persistent state backend | Accepted |
| 0004 | apps/site (Next.js) and apps/web (Vite) split | Accepted |
| 0005 | PolyCo.World renderer — HTML5 Canvas 2D for v0 | Accepted |
| 0006 | Audio engine — Web Audio API + OscillatorNode pair | Accepted |
