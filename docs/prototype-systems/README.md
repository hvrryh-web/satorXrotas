[Ver001.000]

# Prototype Systems (PS-XXX)

One spec per module. Each PS captures the *system's surface*: what it does, what it owns, what it doesn't, where it integrates, what its risks are. Implementation lives in code; behavior lives here.

## Convention

- Filename: `PS-XXX-<kebab-slug>.md`. Three-digit zero-padded.
- PS-001..099 reserved for the seven product modules.
- PS-100+ for additional prototype systems added later (recommenders, A/B engines, etc.).

## Required Sections

1. **Status** (Draft / Approved / Live / Deprecated)
2. **Owner** (role + agent or human)
3. **Phase** (when it lands)
4. **Surface** (what's exposed to apps + other packages)
5. **Domain types** (link to SCHEMA_REGISTRY entries)
6. **Integration points** (vaultbrain events, API endpoints)
7. **Risks** (what could break, what's untested)
8. **Verification** (how we know it works)
9. **Out of scope**

## Index

| ID | Module | Package | Phase | Status |
|----|--------|---------|-------|--------|
| PS-001 | Focus Hero | `@njz-os/focus-engine` | 1 | Draft |
| PS-002 | Soundscapes | `@njz-os/audio-engine` | 1 | Draft |
| PS-003 | Distraction Blocker | (app + `@njz-os/focus-engine`) | 1 | Draft |
| PS-004 | Writing Space | `@njz-os/writing` | 2 | Draft |
| PS-005 | Micro-Learning | `@njz-os/learning-cards` | 2 | Draft |
| PS-006 | Brain Training | `@njz-os/analytics` + games | 2 | Draft |
| PS-007 | PolyCo.World | `@njz-os/polyworld` + `@njz-os/pixel-art` | 1 (shell) → 2 → 3 | Draft |
