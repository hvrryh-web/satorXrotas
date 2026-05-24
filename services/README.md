# services/

RAT-OS-owned backend services. Most NJZ platform services live in upstream `notbleaux/ZeSporteXte` — *that's intentional*. This directory only houses services that are uniquely RAT-OS concerns.

## Members

| Service | Purpose | Phase |
|---------|---------|-------|
| `rat-os-api` | BFF aggregator for the webapp | 2+ |

## Why Most Services Live Upstream

- `services/vaultbrain` — persistent state. Shared by both products.
- `services/agent-gateway` — agent + MCP routing. Shared.
- `services/api` — REST data plane. Shared.
- `services/identity` (TBD) — auth. Shared.

Duplicating these would split user identity and double maintenance. See ADR-0002 and `docs/architecture/INTEGRATION_WITH_ZESPORTEXTE.md`.
