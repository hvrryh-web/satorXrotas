[Ver001.000]

# ADR-0003 — Vaultbrain as Persistent State Backend

- **Status:** Accepted
- **Date:** 2026-05-24
- **Deciders:** @hvrryh-web
- **Tags:** state, persistence, integration

## Context

RAT-OS needs persistent, cross-device state for: focus sessions, streaks, XP, cognitive profile, PolyCo.World scene snapshots, distraction-block schedules, soundscape favorites, manuscript metadata (full text in API), card-deck progress, and AI memory for in-app helpers.

The upstream `notbleaux/ZeSporteXte` already runs a service called `vaultbrain` that provides exactly this — persistent state + AI memory with WebSocket fan-out. Building our own would duplicate effort and split the user's identity between two stores.

## Decision

Vaultbrain (in upstream) is the persistent state backend for RAT-OS. Access is exclusively through `packages/adapters/vaultbrain-client`. No module imports vaultbrain directly.

Local-first behavior layered on top: focus engine and audio engine work fully offline; events are queued and flushed when vaultbrain is reachable.

## Consequences

**Positive:**

- Single source of truth across NJZ products (eSports + RAT-OS) — user can have a unified profile.
- Reuse battle-tested upstream infra.
- WebSocket fan-out gives us cross-device sync for free.
- AI memory primitives already designed in upstream.

**Negative:**

- Hard dependency on upstream availability. Mitigation: local-first + queued mutations.
- Schema evolution coordinated with upstream owners.
- Latency varies with network; affects PolyCo.World decoration animation timing.

**Neutral:**

- We don't own the vaultbrain implementation. We own the adapter and our consumption pattern.

## Alternatives Considered

- **Build RAT-OS's own state service** (Postgres + Redis behind FastAPI). Rejected: duplication, splits user identity, $0-budget posture violated.
- **Browser-only persistence (IndexedDB + service worker).** Rejected: no cross-device sync, no AI memory.
- **Third-party BaaS** (Supabase, Convex, Liveblocks). Rejected: cost, vendor lock-in, doesn't align with upstream platform.

## Related

- ADR-0002 (Consume @njz/* packages)
- `docs/architecture/DATA_FLOW.md`
- `packages/adapters/vaultbrain-client/README.md` (TBD)
