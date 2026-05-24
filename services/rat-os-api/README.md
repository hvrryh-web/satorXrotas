# @njz-os/rat-os-api

Backend-For-Frontend aggregator for RAT-OS. Phase 2+.

## Why

- Aggregates vaultbrain + api + agent-gateway calls into shapes the webapp needs.
- Hides server-only secrets.
- Server-side rendering of premium exports (DOCX).
- Premium-tier gate enforcement that can't be trusted to the client.

## Phase 0

Type declarations only. No runtime.

## Phase 2 Implementation

Stack TBD via ADR (Hono vs Fastify vs Express). Deployment: Render. See `docs/operations/DEPLOYMENT.md`.
