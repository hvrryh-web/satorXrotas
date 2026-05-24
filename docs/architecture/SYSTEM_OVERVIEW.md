[Ver001.000]

# System Overview — NJZ RAT-OS

> Higher-level than `ARCHITECTURE.md`; closer to "what would I draw on a whiteboard?". For decisions, see `ADR/`.

## Three-Layer Mental Model

```
┌──────────────────────────────────────────────────────────────────┐
│  L1 — Surfaces                                                   │
│     apps/site         apps/web        apps/desktop-widget        │
│     (Next.js 15)      (Vite + R19)    (Tauri, Phase 2+)          │
└────────────────────────────┬─────────────────────────────────────┘
                             │ imports
┌────────────────────────────▼─────────────────────────────────────┐
│  L2 — Domain (RAT-OS-local)                                      │
│     @njz-os/core, ui, focus-engine, audio-engine, polyworld,     │
│     pixel-art, progression, analytics, learning-cards, writing   │
└────────────────────────────┬─────────────────────────────────────┘
                             │ imports
┌────────────────────────────▼─────────────────────────────────────┐
│  L3 — Adapters (boundary with platform)                          │
│     vaultbrain-client, agent-gateway-client, api-client,         │
│     identity-client                                              │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTP / WebSocket
┌────────────────────────────▼─────────────────────────────────────┐
│  Platform (notbleaux/ZeSporteXte)                                │
│     services/vaultbrain   services/agent-gateway                 │
│     services/api          services/identity (TBD)                │
│     packages/@njz/*       (npm scope, also consumed by L2)       │
└──────────────────────────────────────────────────────────────────┘
```

## Runtimes

| Surface | Runtime | Hosting |
|---------|---------|---------|
| `apps/site` | Node.js 20 (Next.js App Router) | Vercel (edge + serverless) |
| `apps/web` | Browser (ES2022, Vite-bundled) | Vercel (static + SPA) |
| `apps/desktop-widget` | Tauri (Rust shell + WebView) | User device (Phase 2+) |
| `services/rat-os-api` | Node.js 20 (Hono or Express — TBD ADR) | Render (Phase 2+) |

## State

| State kind | Where it lives | How RAT-OS accesses |
|-----------|----------------|---------------------|
| Ephemeral UI state | React component state, Zustand | Direct |
| Server cache / queries | TanStack Query | `packages/adapters/api-client` |
| Persistent user state | Vaultbrain (upstream) | `packages/adapters/vaultbrain-client` (HTTP + WebSocket) |
| AI memory / context | Vaultbrain | Same |
| Auth session | HttpOnly cookie + refresh in vaultbrain | `packages/adapters/identity-client` (TBD) |
| Local-first cache | IndexedDB (via Dexie) | `@njz-os/core/storage` (Phase 2+) |

## Data Flow — Path A (Live, low-latency)

```
User action in apps/web
  → @njz-os/focus-engine / audio-engine / polyworld emits event
  → vaultbrain-client (WebSocket) → services/vaultbrain
  → state update fan-out → other connected sessions (cross-device sync)
```

## Data Flow — Path B (Authoritative, high-fidelity)

```
User action in apps/web
  → React Server Component or TanStack Query mutation
  → api-client (HTTPS) → services/api
  → Postgres write → response
  → cache invalidate → re-render
```

## Why The Adapter Layer Exists

- Absorbs upstream change. If `services/vaultbrain` changes its protocol, we change the adapter; modules don't notice.
- Enforces network discipline: retries, timeouts, error envelopes, schema validation.
- Gives us a place to inject test doubles (`msw`) without touching modules.
- Single place to add observability (request timing, error rates).

## Asset Pipeline

| Asset type | Source | Storage | Loaded by |
|-----------|--------|---------|-----------|
| Pixel art tiles & sprites | `apps/web/public/sprites/` | Static CDN | `@njz-os/polyworld` |
| Soundscape stems | `apps/web/public/audio/stems/` (Phase 1); CDN (Phase 2+) | Static CDN → R2 (Phase 2+) | `@njz-os/audio-engine` |
| Learning card illustrations | CDN (R2 + KV catalog — Phase 2+) | R2 | `@njz-os/learning-cards` |
| Generative canvases | Generated client-side; saved to user gallery | Vaultbrain (Phase 2+) | `@njz-os/audio-engine` |

## Build / Deploy Topology

```
PR open → CI (lint + typecheck + unit + e2e smoke)
       → Vercel preview (apps/site + apps/web)
       → Comment on PR with preview URL
PR merge to main → Vercel production deploy (apps/site + apps/web)
              → Render deploy (services/rat-os-api — Phase 2+)
Release tag → CHANGELOG.md regenerated; deploy notes posted
```

## See Also

- `INTEGRATION_WITH_ZESPORTEXTE.md` — contract surface and dependencies.
- `DATA_FLOW.md` — detailed event/data flow diagrams.
- `MODULE_BOUNDARIES.md` — what each package can and cannot do.
- `ADR/` — all architecture decisions with rationale.
