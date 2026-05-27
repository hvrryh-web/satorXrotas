[Ver001.000]

# ADR-0014 — Vendor Agent-Gateway `openapi.json` as RAT-OS Contract Source

- **Status:** Accepted
- **Date:** 2026-05-24
- **Deciders:** @hvrryh-web
- **Tags:** contracts, agent-gateway, openapi, vendoring, phase-4-prep
- **Protects gate:** `G4.ai-personalization` (Phase 4 — prep work only in Phase 1)

## Context

`services/agent-gateway` in `notbleaux/ZeSporteXte` is a substantial agent-orchestration service (`app.py` 23 KB plus brain.py, blackboard.py, vault.py, async_bus.py, vaultbrain_adapter.py, supabase_mirror.py, telemetry_monitor.py). It ships its own `openapi.json` at 30 KB — the platform team already authors the contract; we don't need to write one.

RAT-OS will consume agent-gateway during Phase 4 (AI personalisation: adaptive difficulty, content recommendations, in-app helpers — per docs/product/ROADMAP.md). Phase 1 does not consume it, but **the contract surface should be vendored now** so:

- Future contributors can read it without leaving the repo.
- Type generation infrastructure is in place when Phase 4 starts.
- Schema drift between vendored and upstream can be tracked via a CI guard.
- `packages/adapters/agent-gateway-client` types can be regenerated against the same source the upstream team owns.

Two options for "vendoring" exist:

1. Copy `openapi.json` verbatim, with a header noting the upstream SHA it was copied from.
2. Reference the upstream file by URL at build time (fetch on `pnpm install`).

Option 2 fails offline builds, fails airgapped CI runners, and creates a hidden network dependency in the install path. Option 1 is honest about what we depend on at a given commit.

## Decision

**Vendor `services/agent-gateway/openapi.json` into `contracts/openapi/agent-gateway.yaml`** (YAML form for diff readability) at a pinned upstream commit SHA. Periodic refresh via a tool script.

### Mechanics

1. Copy the file:
   ```bash
   curl -sL https://raw.githubusercontent.com/notbleaux/ZeSporteXte/<sha>/services/agent-gateway/openapi.json \
     | yq -P > contracts/openapi/agent-gateway.yaml
   ```
2. Prepend a header to the vendored file:
   ```yaml
   # VENDORED — DO NOT HAND-EDIT.
   # Source: notbleaux/ZeSporteXte/services/agent-gateway/openapi.json
   # Pinned upstream SHA: <40-char SHA>
   # Pinned at: YYYY-MM-DD by <agent>
   # Refresh via: pnpm contracts:refresh-agent-gateway
   ```
3. Add `tools/contracts/refresh-agent-gateway.mjs` that re-runs the curl + yq pipeline against the latest upstream `main` SHA, updates the header, and exits 1 if the diff is non-empty (CI sees the contract changed).
4. Add `pnpm contracts:refresh-agent-gateway` script in root `package.json`.

### Generation target (Phase 4)

When `G4.ai-personalization` unlocks, `packages/adapters/agent-gateway-client` adds a generation step:

```bash
pnpm --filter @njz-os/adapters-agent-gateway-client generate
# Reads contracts/openapi/agent-gateway.yaml
# Writes packages/adapters/agent-gateway-client/src/generated/
# Same convention as packages/adapters/api-client/
```

Generator: `openapi-typescript` (TypeScript types only) + a thin runtime client in `src/client.ts`. The Phase-0 stub at `packages/adapters/agent-gateway-client/src/index.ts` is replaced behind the gate; until then, the vendored YAML is documentation-only.

### Drift detection

CI workflow `.github/workflows/contracts-drift.yml` (new) runs weekly:

- Fetches the latest upstream `openapi.json`.
- Diffs against the vendored YAML (after `yq -P` normalisation).
- If non-empty diff, opens an issue tagged `contracts-drift` with the diff as the body.

Drift is **not** a build break — it's informational. The decision to update the pin is human; the decision to follow upstream changes might be "no" if a change is unsafe.

### What lives in `contracts/openapi/` after this ADR

```
contracts/openapi/
  njz-rat-os.yaml         # OUR consumer-side mirror (existing; describes the
                          # vaultbrain endpoint shape RAT-OS depends on after
                          # ADR-0008's upstream extension lands).
  agent-gateway.yaml      # VENDORED from upstream openapi.json (this ADR).
```

If `services/api` (upstream) ever publishes its own OpenAPI spec, a follow-up ADR vendors it the same way.

## Consequences

**Positive:**

- Single source of truth for the agent-gateway surface, in our repo, at a known pin.
- Future Phase-4 work can begin with codegen the day the gate opens.
- Drift detection without blocking builds — informational, agent-driven follow-up.
- Reproducible: anyone can regenerate the vendored file from the pinned SHA.

**Negative:**

- Maintenance overhead: we own the pin, we own the refresh discipline.
- Vendored file can fall behind upstream silently if drift checks aren't reviewed; the weekly issue is the safety net.
- 30 KB of vendored YAML in the repo. Acceptable.

**Neutral:**

- The vendored YAML is dead code from a runtime perspective until Phase 4. That's intentional — we're staging the contract, not the consumer.
- `tools/contracts/refresh-agent-gateway.mjs` is a write-rare script; not bundled with apps.

## Alternatives Considered

- **Fetch upstream at build time.** Rejected: hidden network dep in the install path; breaks offline + airgapped CI; install determinism suffers.
- **`git subtree` of the upstream `services/agent-gateway/` directory.** Rejected: pulls in 100+ KB of Python code we don't run; conflates our repo with upstream code; ADR-0002 already rules out submodule/copy at the package level.
- **Skip vendoring; defer until Phase 4 starts.** Rejected: when Phase 4 opens, we want immediate codegen unblocked; setting up the pipeline now costs little and pays back when the gate flips.
- **Vendor as `.json` not `.yaml`.** Rejected: JSON diffs are worse to review (no line breaks at logical boundaries); YAML round-trips cleanly via `yq`.
- **Maintain our own consumer-side mirror like `njz-rat-os.yaml` for agent-gateway.** Rejected: agent-gateway is large and rapidly evolving; reauthoring its contract is wasted effort when the upstream spec is canonical and machine-generated.

## Related

- ADR-0002 — Consume `@njz/*` packages from upstream (sets the precedent that we wrap upstream surfaces in adapters; vendored OpenAPI is consistent with that).
- ADR-0008 — Vaultbrain integration shape (which keeps its own `njz-rat-os.yaml` because that surface is small and consumer-defined; agent-gateway is the opposite case).
- `packages/adapters/agent-gateway-client/README.md` — Phase-0 stub; Phase-4 codegen target.
- `contracts/openapi/agent-gateway.yaml` — new vendored file.
- `tools/contracts/refresh-agent-gateway.mjs` — new tool script.
- `.github/workflows/contracts-drift.yml` — new CI workflow.
- Upstream source: `notbleaux/ZeSporteXte/services/agent-gateway/openapi.json`.

---

> When proposing, leave Status: Proposed. On approval, change to Accepted in a follow-up commit.
> Append a one-line entry to `.agents/DECISION_LOG.md` referencing this ADR.
