[Ver001.000]

# Upstream Coordination — `notbleaux/ZeSporteXte`

**Channel:** `framework` + `adapters`
**Status:** active
**Tracks:** ADR-0007 (`@njz/ui` publish), ADR-0008 (vaultbrain extension)
**Owner role:** Coordinator + Data Engineer
**Opened:** 2026-05-24

---

## Why this file exists

Two ADRs in the bootstrap PR (`claude/gracious-mayer-Emj1S → main`) defer
implementation work pending upstream changes:

- **ADR-0007** — `@njz/ui` consumption deferred until upstream publishes a
  real package.
- **ADR-0008** — Vaultbrain extension (schema + endpoints + WS fan-out)
  needed before `packages/adapters/vaultbrain-client` can ship a real
  implementation.

This file is the single source of truth for the cross-repo coordination
threads. Update it on every upstream interaction.

---

## Thread 1 — `@njz/ui` upstream publish (for ADR-0007)

### Ask

Upstream finishes `packages/@njz/ui` as a real, consumable package:

- `package.json` with `name: "@njz/ui"`, `version`, `main`/`types` entries.
- `tsconfig.json` referencing the upstream shared tsconfig.
- `src/index.ts` re-exporting the initial primitive set (Button, Panel,
  Toggle).
- A semver-tagged release on GitHub Packages (or the registry RAT-OS will
  install from).
- A short README documenting the primitive surface.

### Issue to file (upstream)

Repo: `notbleaux/ZeSporteXte`
Title: `[@njz/ui] Publish package — needed by hvrryh-web/satorXrotas (NJZ RAT-OS)`
Labels: `@njz/ui`, `packaging`, `cross-repo`.
Body:

> RAT-OS is consuming the upstream `@njz/*` scope per ADR-0002. We're
> ready to depend on `@njz/ui` for shared design primitives, but
> `packages/@njz/ui/` currently has only `src/components/` — no
> `package.json`, no exported surface, no published version.
>
> RAT-OS captured the deferral in ADR-0007
> (`docs/architecture/ADR/ADR-0007-njz-ui-deferred.md`). When `@njz/ui`
> ships, RAT-OS will open a follow-up ADR to migrate from
> `@njz-os/ui` (currently self-contained) to consumption of the upstream
> primitive surface.
>
> Concretely needed: `package.json`, `tsconfig.json`, `src/index.ts`
> with at least Button/Panel/Toggle exported, a semver-tagged release.

### Status

- [ ] Issue filed (link: _TBD_)
- [ ] Acknowledged by upstream
- [ ] Package published
- [ ] RAT-OS migration ADR opened
- [ ] `@njz-os/ui` deprecated in favour of `@njz/ui` (Phase 2/3)

---

## Thread 2 — Vaultbrain extension (for ADR-0008)

### Ask

Extend `services/vaultbrain` with the user-state surface RAT-OS needs.
Schema delta + endpoint additions + real WebSocket fan-out via Redis
pub/sub. Full spec in ADR-0008.

### Schema delta (`services/vaultbrain/schema/`)

```
users                  (id, display_name, tier, created_at, deleted_at)
sessions               (id, user_id, module_slug, mode, started_at, ended_at,
                        duration_ms, state, metadata jsonb)
streaks                (id, user_id, module_slug, current_days, longest_days,
                        last_active_at)
progression_events     (id, user_id, kind, payload jsonb, occurred_at)
                       — append-only
cognitive_profiles     (user_id, memory, attention, speed, flexibility, spatial,
                        updated_at)
```

RLS and partitioning consistent with existing `vaults`/`notes` tables.

### Endpoint additions (`services/vaultbrain/main.py`)

```
GET  /users/{id}/progression       → ProgressionState (xp + streaks)
POST /sessions/start               → create session row, state=running
POST /sessions/{id}/complete       → close session, emit progression_event,
                                     return updated state
POST /sessions/{id}/abandon        → close session, state=abandoned, no XP
GET  /streaks/{user_id}            → per-module StreakState map
GET  /users/{id}/profile           → CognitiveProfile vector
```

Auth/CORS pattern: same as existing routes.

### WebSocket fan-out

Replace the echo in `/ws/sync` (or add a new `/ws/progression`). Redis
pub/sub. Channel pattern: `progression:{user_id}`. Handshake:

```jsonc
// client → server
{ "subscribe": "<user_id>", "token": "<jwt>" }

// server → client (on success)
{ "subscribed": "<user_id>" }

// server → client (event)
{ "kind": "session.complete", "userId": "...", "at": "...", "payload": {...} }
```

### Issue to file (upstream)

Repo: `notbleaux/ZeSporteXte`
Title: `[vaultbrain] User-state extension — needed by hvrryh-web/satorXrotas (NJZ RAT-OS)`
Labels: `vaultbrain`, `schema`, `websocket`, `cross-repo`.
Body:

> RAT-OS captured the integration shape it needs in ADR-0008
> (`docs/architecture/ADR/ADR-0008-vaultbrain-integration-shape.md`). The
> current vaultbrain surface (vaults/notes/sync/oversight) doesn't carry
> user-state primitives (sessions, streaks, XP, progression events,
> cognitive profile) and the WebSocket is currently an echo placeholder.
>
> Proposing: schema delta + endpoint additions + real WS fan-out via Redis
> pub/sub. Detailed spec in the ADR linked above. Happy to draft the PR
> against vaultbrain if alignment on the schema is reached here first.

### Status

- [ ] Issue filed (link: _TBD_)
- [ ] Schema delta reviewed by upstream owners
- [ ] Endpoint shape reviewed
- [ ] WS protocol reviewed
- [ ] Upstream PR opened (RAT-OS-drafted or upstream-drafted)
- [ ] Upstream PR merged
- [ ] `packages/adapters/vaultbrain-client` real implementation lands in RAT-OS
- [ ] G1.vaultbrain-live flipped to OPEN in `.agents/PHASE_GATES.md`

### Fallback path (ADR-0008 Option B)

If upstream coordination stalls > 2 weeks from issue filing:

- Build `services/rat-os-state` in this repo (Postgres + FastAPI mirror).
- Same client surface (`packages/adapters/vaultbrain-client` still the only
  consumer touch-point — adapter URL changes, contract doesn't).
- Document the pivot in a follow-up ADR and update PHASE_GATES.

---

## Cadence

- Check thread status weekly (Friday) during Phase 0–1.
- Bump to bi-weekly when both threads close.
- This file is T1 (load on demand). Closed threads get moved to a dossier
  per `.agents/archiving/DOSSIER_CREATION_TEMPLATE.md`.

---

## See Also

- `docs/architecture/ADR/ADR-0007-njz-ui-deferred.md`
- `docs/architecture/ADR/ADR-0008-vaultbrain-integration-shape.md`
- `docs/architecture/INTEGRATION_WITH_ZESPORTEXTE.md`
- `.agents/COORDINATION_PROTOCOL.md`
