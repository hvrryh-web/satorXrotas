[Ver001.000]

# STD-02 — Naming Standards

## Brand Surfaces

| Context | Use |
|---------|-----|
| Marketing copy, README headlines, social posts | **NJZ RAT-OS** |
| Documentation prose (general) | NJZ RAT-OS |
| Code, package names, paths, schemas | `njz-os`, `@njz-os/*` |
| URL host (TBD) | `njz-os.{net,app,com}` |
| Repository name | `satorXrotas` (kept for continuity) |

Never write `NJZRATOS`, `NjzRatOs`, `njz_rat_os`. Choose `NJZ RAT-OS` (display) or `njz-os` (code).

## Package Scopes

- `@njz/*` — shared cross-product packages defined in `notbleaux/ZeSporteXte`. Consume; do not redefine.
- `@njz-os/*` — RAT-OS-specific packages defined here.

## Module Names

The seven product modules are referred to as:

- `focus-hero` (gamified focus timer)
- `soundscapes` (audio + binaural)
- `distraction-blocker` (blocker)
- `writing-space` (manuscript editor)
- `micro-learning` (card-based lessons)
- `brain-training` (cognitive games)
- `polyco-world` (metaverse)

Use these slugs in directory names, package names, route paths, and event names. No alternative spellings.

## Phases & Gates

- Phases: `Phase 0`, `Phase 1`, … (display). `phase-0`, `phase-1`, … (slugs).
- Gates: `G<phase>.<slug>` (e.g. `G1.focus-hero`).

## ADR Numbering

- `ADR-XXXX-<kebab-slug>.md`. Four-digit zero-padded. Monotonic.
- Don't skip numbers. Don't reuse a number for a different topic.

## Dev Report Numbering

- `DR-XXXX-<kebab-slug>.md`. Four-digit zero-padded. Monotonic.

## Prototype System Numbering

- `PS-XXX-<kebab-slug>.md`. Three-digit zero-padded. PS-001..PS-007 reserved for the seven modules; PS-100+ for new prototype systems.

## Session Workplans

- `SW-YYYYMMDD-<kebab-slug>.md`.

## Branches

- `feat/<area>-<short-name>`
- `fix/<area>-<bug>`
- `docs/<area>-<topic>`
- `infra/<area>`
- `chore/<area>-<task>`
- `<agent-tool>/<topic>` for agent-driven work (e.g. `claude/feature-x`)
- `legacy/<archive-name>` reserved for archive branches

## Environment Variables

- `SCREAMING_SNAKE_CASE`.
- Public/runtime: `NEXT_PUBLIC_*` (Next.js), `VITE_*` (Vite).
- Server-only: no prefix.
- Document every var in `.env.example` (no real values).
