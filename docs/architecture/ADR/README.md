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

## Index

| ID | Title | Status |
|----|-------|--------|
| 0001 | Monorepo structure & brand naming | Accepted |
| 0002 | Consume `@njz/*` packages from upstream (no submodule, no fork) | Accepted — partially superseded by ADR-0007 |
| 0003 | Vaultbrain as persistent state backend | Superseded by ADR-0008 |
| 0004 | apps/site (Next.js) and apps/web (Vite) split | Accepted |
| 0005 | PolyCo.World renderer — HTML5 Canvas 2D for v0 | Accepted |
| 0006 | Audio engine — Web Audio API + OscillatorNode pair | Accepted |
| 0007 | `@njz/ui` consumption deferred until upstream publishes | Accepted |
| 0008 | Vaultbrain integration shape (supersedes ADR-0003) | Accepted |
| 0009 | Focus Engine state machine (XState v5) | Accepted |
| 0010 | Audio Engine v0 detail (stems, crossfade, binaural, FFT) | Accepted |
| 0011 | Distraction Blocker enforcement (web SW + browser extension; native deferred) | Accepted |
| 0012 | Asset pipeline (Aseprite + FFmpeg → public/; R2 in Phase 2) | Accepted |
| 0013 | Auth model (passkeys + email via Supabase Auth) | Accepted |
| 0014 | Vendor agent-gateway `openapi.json` as RAT-OS contract source | Accepted |
