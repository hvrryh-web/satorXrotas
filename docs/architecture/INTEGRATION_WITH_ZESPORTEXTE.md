[Ver001.000]

# Integration With ZeSporteXte

> RAT-OS and ZeSporteXte are sibling NJZ products. ZeSporteXte is the platform monorepo; RAT-OS consumes a defined subset of its capabilities. This doc is the contract.

## Repository Map

| Repo | URL | Role | Owner |
|------|-----|------|-------|
| `notbleaux/ZeSporteXte` | https://github.com/notbleaux/ZeSporteXte | Platform monorepo (eSports product + shared NJZ infra) | Platform team |
| `hvrryh-web/satorXrotas` | https://github.com/hvrryh-web/satorXrotas | NJZ RAT-OS (this repo) | RAT-OS team |

## What We Consume

### Packages (npm scope `@njz/*`)

| Package | Source path in upstream | Used in RAT-OS |
|---------|-------------------------|----------------|
| `@njz/ui` | `packages/@njz/ui` | Re-exported by `@njz-os/ui` for shared design primitives |
| `@njz/vaultbrain-events` (planned) | `packages/@njz/vaultbrain-events` | Type definitions wrapped by `packages/adapters/vaultbrain-client` |
| `@njz/agent-protocol` (planned) | `packages/@njz/agent-protocol` | Type definitions wrapped by `packages/adapters/agent-gateway-client` |
| `@njz/auth-types` (planned) | `packages/@njz/auth-types` | Identity types for `packages/adapters/identity-client` |

Version pinning: `^x.y.z` with explicit `pnpm.overrides` lock if needed. Bump via PR; never auto-update.

### Services (HTTP / WebSocket)

| Service | Upstream path | RAT-OS adapter | Protocol | Why |
|---------|---------------|----------------|----------|-----|
| Vaultbrain | `services/vaultbrain` | `packages/adapters/vaultbrain-client` | WebSocket (live) + HTTP (CRUD) | Persistent state, AI memory, cross-device sync |
| Agent Gateway | `services/agent-gateway` | `packages/adapters/agent-gateway-client` | HTTP | In-app AI helpers; MCP routing |
| API | `services/api` | `packages/adapters/api-client` | HTTPS | REST data plane; OpenAPI-generated client |
| Identity (TBD) | TBD | `packages/adapters/identity-client` | HTTPS | Auth / session management |

## Contract Surface

The complete list of endpoints RAT-OS depends on lives in `contracts/openapi/njz-rat-os.yaml`. Event schemas live in `contracts/events/`. The upstream is the source of truth; we mirror only what we use.

When the upstream adds an endpoint:

- It is *not* automatically part of our surface.
- To depend on it, we add it to `njz-rat-os.yaml` and regenerate the client.

When the upstream removes / changes an endpoint we depend on:

- Upstream is expected to deprecate first (1 minor version notice).
- We track upstream release notes weekly.
- We absorb the change in the adapter; modules don't notice unless type changes.

## What We Don't Touch

Out of scope from upstream:

- `apps/web/src/hub-1-sator/`, `hub-2-rotas/`, `hub-3-arepo/`, `hub-4-opera/`, `hub-5-tenet/` — eSports product hubs.
- `apps/VCT Valorant eSports/`, `apps/browser-extension/`, `apps/companion/`, `apps/overlay/`, `apps/nexus/`, `apps/wiki/` — eSports apps.
- `services/exe-directory/`, `services/hermes-host/`, `services/legacy-compiler/`, `services/tenet-verification/`, `services/websocket/` — eSports-specific services.
- `packages/@esportexe/*` — eSports-only packages.
- `platform/simulation-game/` (Godot) — eSports simulation engine.
- `axiom_esports_data/`, `data/schemas/GameNodeID.ts`, `data/schemas/tenet-protocol.ts` — eSports data schemas.

## What We *Cross-Use*

Some upstream apps overlap with RAT-OS thematically:

- `apps/polyoffice/` — pixel-art productivity surface in upstream. May share design language with RAT-OS PolyCo.World Office. **Action:** confirm with upstream owner; consider sharing pixel-art assets via `@njz/polyworld-assets` (TBD).
- `apps/hexnex/` — name suggests connectivity / hex grid; status unclear. **Action:** investigate, may or may not relate.
- `apps/nexus/` — similar question.

These cross-cuts are tracked via issues in upstream and `.agents/handoff/zesportexte-coordination.md` here.

## Versioning Discipline

| Change type | Process |
|-------------|---------|
| Add adapter method | PR in RAT-OS; no upstream change |
| Bump `@njz/*` minor | PR in RAT-OS bumping `package.json`; smoke test |
| Bump `@njz/*` major | ADR + PR; full integration test against staging |
| Change RAT-OS contract surface | PR in RAT-OS; notify upstream owners |
| Request new upstream endpoint | Open issue in upstream; pause RAT-OS work until accepted |

## Local Development Story

For developers who want both repos cloned side by side:

```
parent/
├── ZeSporteXte/         # upstream
└── satorXrotas/         # RAT-OS
```

Optional: use `pnpm` overrides to point `@njz/*` to local paths:

```jsonc
// satorXrotas/package.json
{
  "pnpm": {
    "overrides": {
      "@njz/ui": "link:../ZeSporteXte/packages/@njz/ui"
    }
  }
}
```

This is a developer convenience only. CI always installs from the registry.

## Failure Modes & Mitigation

| Failure | Detection | Mitigation |
|---------|-----------|------------|
| Upstream service down | Adapter health checks fail | Show degraded-mode UI; queue mutations |
| Upstream schema change unnoticed | Generated client regen produces a diff | Pre-commit on contracts compares against upstream snapshot |
| Version drift between RAT-OS and upstream `@njz/*` | Renovate / Dependabot | Weekly bump review |
| Coordination friction | — | Quarterly cross-team sync; `.agents/handoff/zesportexte-coordination.md` |
