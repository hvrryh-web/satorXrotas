[Ver001.000]

# ADR-0008 — Vaultbrain Integration Shape (Supersedes ADR-0003)

- **Status:** Accepted
- **Date:** 2026-05-24
- **Deciders:** @hvrryh-web
- **Tags:** state, persistence, integration, upstream-coordination, vaultbrain, supersession

## Context

ADR-0003 ("Vaultbrain as Persistent State Backend") committed RAT-OS to using the upstream `services/vaultbrain` for all user-domain state: focus sessions, streaks, XP, cognitive profile, PolyCo.World scene snapshots, distraction-block schedules, soundscape favourites, manuscript metadata, deck progress, and AI memory. The ADR described vaultbrain as "persistent state + AI memory with WebSocket fan-out."

Reality check against `notbleaux/ZeSporteXte` post-bootstrap reveals a different shape than ADR-0003 assumed:

- Vaultbrain is **a multi-vault networked note system** for agent-and-Eli oversight, not a generic user-state store. Its title in `services/vaultbrain/main.py` is "Multi-vault networked note system with agent oversight."
- Live endpoints (FastAPI on `:8001`):
  - `GET /health`
  - `GET /vaults` and `GET /vaults/{vault_id}`
  - `GET|POST /vaults/{vault_id}/notes`, `GET|PUT|DELETE /vaults/{vault_id}/notes/{note_id}`
  - `GET /sync/queue`, `POST /sync/approve`, `POST /sync/reject`
  - `GET /oversight/dashboard`, `GET /oversight/activity`
  - `WebSocket /ws/sync` — **placeholder echo**, no real fan-out yet
- Database tables: `vaults`, `notes`, `note_links`, `sync_queue`, `deletion_log` (per `services/vaultbrain/schema/` and the README).
- No tables, endpoints, or events for `users`, `sessions`, `streaks`, `progression_events`, or `cognitive_profiles` — the data model RAT-OS needs.

Three viable shapes for getting RAT-OS the persistence it needs.

## Decision

**Option A: Extend vaultbrain upstream with a user-state surface.** This is the chosen path. Concretely:

1. **Schema extension** (`services/vaultbrain/schema/`):
   - `users` — id, display_name, tier, created_at, deleted_at
   - `sessions` — id, user_id, module_slug, mode, started_at, ended_at, duration_ms, state, metadata jsonb
   - `streaks` — id, user_id, module_slug, current_days, longest_days, last_active_at
   - `progression_events` — id, user_id, kind, payload jsonb, occurred_at (append-only)
   - `cognitive_profiles` — user_id, dimension vector (memory, attention, speed, flexibility, spatial), updated_at
   - RLS / partitioning consistent with existing vaults/notes patterns.

2. **Endpoint extension** (`services/vaultbrain/main.py`):
   - `GET /users/{id}/progression` — returns `ProgressionState` (xp + streaks across all module slugs)
   - `POST /sessions/start` — creates a `sessions` row in state=`pending` → `running`
   - `POST /sessions/{id}/complete` — closes a session, emits a `progression_events` row, returns updated state
   - `POST /sessions/{id}/abandon` — same as complete but state=`abandoned`, no XP awarded
   - `GET /streaks/{user_id}` — returns the per-module `StreakState` map
   - `GET /users/{id}/profile` — returns the cognitive profile vector
   - All new endpoints respect the same auth/CORS pattern as existing routes.

3. **Real WebSocket fan-out** (`services/vaultbrain/main.py` `/ws/sync` or a new `/ws/progression`):
   - Replace the echo with Redis pub/sub fan-out.
   - Channel pattern: `progression:{user_id}` — events broadcast to all sockets subscribed for that user.
   - Subscription handshake: client sends `{ "subscribe": "<user_id>", "token": "<jwt>" }`; server validates and joins the channel.

4. **Coordination via upstream issue + PR.** RAT-OS work that depends on this shape (`packages/adapters/vaultbrain-client/src/index.ts` real implementation, Phase 1 module wiring) is gated by the upstream PR landing. Tracked in `.agents/active/upstream-coordination.md`.

**Option B: Build `services/rat-os-state` in this repo.** Fallback if upstream coordination stalls > 2 weeks. Postgres + FastAPI mirror of the same shape described above. Same client adapter, different transport URL. Documented here as an explicit fallback, **not chosen now.**

Either way, the client surface is fixed:

- `packages/adapters/vaultbrain-client` is the **only** place RAT-OS code talks to user-state storage.
- The adapter wraps the network call with retries/timeouts/Zod validation.
- Modules import the adapter, never the underlying transport.

This ADR **supersedes ADR-0003** in full. The "vaultbrain is our state backend" thesis holds; the shape and the integration mechanics needed correcting.

## Consequences

**Positive:**

- Single source of truth for user identity across NJZ products. An eSports user and a RAT-OS user can share the same vaultbrain account; agent-vault overlap with user-vault doesn't create identity bifurcation.
- Preserves the $0-budget posture in `docs/product/PRD.md` §1.4 — no third-party BaaS spend.
- Reuses upstream Postgres + Redis + async infrastructure that already runs.
- The explicit event log (`progression_events` append-only) enables event-sourcing-style replay for analytics and debugging.
- Provides a clean coordination artefact: the upstream PR documents both teams' contract.

**Negative:**

- Hard dependency on upstream availability and on coordination cadence with vaultbrain owners. If they're slow, Phase 1 slows.
- Schema evolution must be coordinated cross-team going forward — a constraint we now own forever.
- WebSocket fan-out via Redis pub/sub adds an infra surface (Redis must be deployed in vaultbrain's environment). Upstream's `docker-compose.yml` already includes Redis but production status is unclear; the upstream PR confirms.
- Latency varies with network; affects PolyCo.World decoration animation timing. Mitigated by local-first behaviour in `@njz-os/focus-engine` and `@njz-os/audio-engine` — they queue and reconcile, never block on vaultbrain.

**Neutral:**

- We don't own the vaultbrain implementation. We own the adapter and our consumption pattern.
- The agent-vault surface (`/vaults`, `/notes`, `/sync/*`, `/oversight/*`) remains entirely upstream-owned and out-of-scope for RAT-OS consumption. Different concern; different consumers.
- AI-memory primitives mentioned in ADR-0003 are now understood to live in `services/agent-gateway` (which has `vault.py`, `blackboard.py`, `brain.py`), not vaultbrain. ADR-0014 (planned) will vendor `services/agent-gateway/openapi.json` for that surface.

## Alternatives Considered

- **Status quo: pretend vaultbrain already has what we need.** Rejected: it doesn't; the schemas don't fit; the WebSocket is an echo. Writing client code against an imaginary surface is worse than acknowledging the gap.
- **Build `services/rat-os-state` in this repo (Option B above).** Faster (no upstream dependency) but creates two stores for the same user identity, doubles maintenance, and undermines the "single platform" thesis. Held as fallback only.
- **Use a third-party BaaS (Supabase, Convex, Liveblocks) for user state.** Rejected: cost in production at any meaningful scale; vendor lock-in; conflicts with the $0-budget posture.
- **Encode user state inside vaultbrain's existing `notes` table as JSON blobs.** Rejected as hacky but considered. Would unblock immediately but produces an un-queryable mess and fights the schema. Acceptable only for a 24-hour spike; not for a production model.
- **IndexedDB-only (browser-local, no server).** Rejected: cross-device sync is a core PRD promise (§2.1.2); browser-local state breaks the "start on mobile, continue on desktop" flow.

## Related

- ADR-0003 — **Superseded by this ADR.** The "vaultbrain is the state backend" intent is preserved; the shape and the integration mechanics are corrected here.
- ADR-0002 — Adapter consumption pattern unchanged; vaultbrain endpoints are reached via `packages/adapters/vaultbrain-client` as that ADR established.
- ADR-0007 (this PR) — Independent reality-check ADR. Both arose from the same post-bootstrap upstream audit.
- ADR-0014 (planned) — Vendor `services/agent-gateway/openapi.json` as `contracts/openapi/agent-gateway.yaml`. Separate concern (agent/AI surface) from this ADR's user-state surface.
- `services/vaultbrain/main.py`, `services/vaultbrain/schema/`, `services/vaultbrain/README.md` (upstream) — the artefacts being extended.
- `packages/adapters/vaultbrain-client/README.md` — Phase-0 stub; real impl follows once upstream PR lands.
- `contracts/openapi/njz-rat-os.yaml` — already enumerates the consumer-side endpoint shape we'll need.
- `docs/architecture/INTEGRATION_WITH_ZESPORTEXTE.md` — referenced from there with a pointer to this ADR.
- `.agents/active/upstream-coordination.md` — tracks the upstream coordination thread.

---

> When proposing, leave Status: Proposed. On approval, change to Accepted in a follow-up commit.
> Append a one-line entry to `.agents/DECISION_LOG.md` referencing this ADR.
