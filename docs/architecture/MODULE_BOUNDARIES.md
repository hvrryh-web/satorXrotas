[Ver001.000]

# Module Boundaries — NJZ RAT-OS

> Authoritative answer to "what can package X import from package Y?". CI enforces these via `eslint-plugin-boundaries`.

## Layered Model

```
L0  contracts/                  — pure schema, no code
L1  packages/adapters/*         — wrap upstream services
L2  packages/@njz-os/core       — domain types, no I/O
L3  packages/@njz-os/{ui, audio-engine, focus-engine, polyworld,
                       pixel-art, progression, analytics,
                       learning-cards, writing}   — feature domains
L4  apps/{site,web,desktop-widget,pwa-shell}      — surfaces
S   services/rat-os-api         — server-side BFF (Phase 2+)
```

## Allowed Imports

| From | May import |
|------|------------|
| `apps/*` | any L3 package, any L1 adapter, `@njz/*` upstream, `contracts/*` types |
| `@njz-os/{audio,focus,polyworld,pixel-art,progression,analytics,learning-cards,writing}` (L3 feature domains) | Other L3 packages, `@njz-os/core` (L2), `@njz-os/ui` (L3), `@njz/*` types from upstream |
| `@njz-os/ui` | `@njz-os/core`, `@njz/ui` upstream |
| `@njz-os/core` | std libs only |
| `packages/adapters/*` (L1) | `@njz-os/core` (L2), `@njz/*` upstream SDK, std libs, `contracts/*` types |
| `services/rat-os-api` (S) | `@njz-os/core`, `packages/adapters/*`, server libs (Hono/Express/Fastify) |

## Forbidden Imports (CI fails)

| From | May NOT import |
|------|----------------|
| Any L3 package | `apps/*`, `services/*` |
| `@njz-os/core` | Other `@njz-os/*` packages (avoid cycles) |
| `packages/adapters/*` | Other `@njz-os/*` packages besides `core` (adapters are thin) |
| `contracts/*` | Anything (it's pure schema) |
| `services/*` | `apps/*` |

## Cyclic Imports

Banned. Period. If you find one, refactor.

## Side-Effect Free Packages

These export only pure functions / types / classes. No top-level side effects:

- `@njz-os/core`
- `@njz-os/progression`
- `@njz-os/analytics`
- All `contracts/*`

`@njz-os/audio-engine`, `@njz-os/polyworld`, and `@njz-os/focus-engine` may instantiate Web APIs but only inside exported factory functions — not at module top level.

## Why These Boundaries

| Boundary | Why |
|----------|-----|
| Apps can't be imported anywhere | Apps are leaves; nothing should depend on a surface |
| Modules can't import services | Modules are isomorphic (could in theory run server-side); services are server-only |
| Adapters are thin | A fat adapter accumulates business logic that should live in modules |
| Core has no cross-module deps | Domain types are the foundation; anything they depend on becomes a foundation too |

## Adding a New Package

When adding `@njz-os/<new>`:

1. Place at L3 by default.
2. Update this matrix if it's not a feature domain.
3. Update the ESLint boundaries config (`packages/config/eslint-config/`).
4. Smoke-test that `pnpm typecheck` still succeeds across the tree.

## Inspecting

```bash
pnpm --filter @njz-os/<package> lint
pnpm boundaries:check        # Run the standalone boundary check (CI invokes this)
```
