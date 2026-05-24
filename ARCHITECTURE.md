[Ver001.000]

# ARCHITECTURE — NJZ RAT-OS

High-level system view. For decisions, see `docs/architecture/ADR/`. For module-by-module behaviour, see `docs/prototype-systems/`.

## Two Surfaces, One Backend

```
┌─────────────────────────────┐       ┌────────────────────────────┐
│   apps/site (Next.js 15)    │       │   apps/web (Vite + React)  │
│   marketing, SSG/ISR        │       │   webapp, 7 modules + RPG  │
└──────────────┬──────────────┘       └──────────────┬─────────────┘
               │ analytics + auth                    │
               └────────────────┬────────────────────┘
                                ▼
                   ┌─────────────────────────┐
                   │ packages/@njz-os/*      │  local domain logic
                   │   focus-engine          │
                   │   audio-engine          │
                   │   polyworld             │
                   │   progression           │
                   │   analytics             │
                   │   learning-cards        │
                   │   writing               │
                   │   ui (design system)    │
                   └────────────┬────────────┘
                                ▼
                   ┌─────────────────────────┐
                   │ packages/adapters/*     │  typed clients (HTTP/WS)
                   │   vaultbrain-client     │
                   │   agent-gateway-client  │
                   │   api-client (OpenAPI)  │
                   │   identity-client       │
                   └────────────┬────────────┘
                                ▼   (HTTP / WebSocket)
                   ┌─────────────────────────┐
                   │ notbleaux/ZeSporteXte   │  upstream platform
                   │   services/vaultbrain   │
                   │   services/agent-gw     │
                   │   services/api          │
                   │   packages/@njz/ui      │  (also consumed via npm)
                   └─────────────────────────┘
```

## Why Two Apps in One Repo

- **`apps/site`** — public marketing surface. Statically generated for fast TTFB + great SEO. Optimised for cold visitors.
- **`apps/web`** — authenticated webapp. SPA-style. Heavy on canvas/audio/3D. Optimised for daily-active users.

They share design tokens (`@njz-os/ui`), analytics adapters, and identity. They do not share routing or runtime.

## Domain Boundaries

| Package | Owns | Does NOT own |
|---------|------|--------------|
| `@njz-os/core` | Plain TS types: `UserId`, `SessionId`, `StreakState`, `CognitiveProfile`, `ProgressionEvent` | I/O, side effects, framework code |
| `@njz-os/focus-engine` | Pomodoro/deep-work state machines (XState) | Audio playback, UI rendering |
| `@njz-os/audio-engine` | Web Audio graph, soundscape loop logic, binaural beat synth | Track *content*, UI, visual canvas |
| `@njz-os/polyworld` | Isometric canvas renderer, scene graph, tile system | Game design (lives in `apps/web/src/modules/polyco-world/`) |
| `@njz-os/progression` | XP / streak / reward calculus | Persistence (delegated to `vaultbrain-client`) |
| `@njz-os/analytics` | Cognitive scoring, percentile bands, profile vector ops | Event transport (lives in adapters) |
| `@njz-os/learning-cards` | Card data model, deck builder, spaced-repetition algorithm | Card *content* (data) |
| `@njz-os/writing` | Manuscript model, chapter trees, export formats | Editor UI (lives in `apps/web/src/modules/writing-space/`) |
| `@njz-os/ui` | Tokens, primitives, Tailwind preset | Page-level layout |

## Data Flow — Two Paths

Same as the upstream platform's convention:

- **Path A (Live):** Webapp ↔ `vaultbrain-client` ↔ `vaultbrain` over WS for real-time session state, streaks, world updates.
- **Path B (Authoritative):** Webapp ↔ `api-client` ↔ `services/api` over HTTPS for cold reads and persisted artefacts (manuscripts, deck progress, exported canvases).

## Integration With ZeSporteXte

The upstream monorepo `notbleaux/ZeSporteXte` provides:

- `@njz/ui` — design primitives we extend in `@njz-os/ui`.
- `services/vaultbrain` — persistent state + AI memory backend.
- `services/agent-gateway` — MCP + agent routing (used by in-app AI helpers).
- `services/api` — REST data plane.

We do not vendor or fork those services. Adapters wrap the network calls and absorb upstream change. Contracts live in `contracts/openapi/njz-rat-os.yaml` (the surface RAT-OS depends on).

See `docs/architecture/INTEGRATION_WITH_ZESPORTEXTE.md` for the full mapping, including which endpoints we touch and our SLA expectations.

## Deployment Topology

| Surface | Host | Notes |
|---------|------|-------|
| `apps/site` | Vercel | SSG/ISR, edge-cached |
| `apps/web` | Vercel | SPA bundle |
| `services/rat-os-api` (BFF) | Render | Phase 2+ |
| Upstream `services/*` | (managed by ZeSporteXte) | We do not deploy these |

CI runs lint + typecheck + tests on every PR. Production deploys are tagged releases only (Phase 1+).

## See Also

- `docs/architecture/INTEGRATION_WITH_ZESPORTEXTE.md`
- `docs/architecture/DATA_FLOW.md`
- `docs/architecture/MODULE_BOUNDARIES.md`
- `docs/architecture/ADR/`
