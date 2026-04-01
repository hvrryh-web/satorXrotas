# api/src/

Placeholder for the SATOR backend API.

## Purpose

The API layer is the **second enforcement point** of the data partition firewall. It
receives match data from the game, applies `FantasyDataFilter.sanitizeForWeb()`, and
exposes only `stats-schema`-compliant responses to the web platform.

## Planned Contents

- `routes/` — Express / Fastify route handlers
- `middleware/` — Firewall middleware (sanitization + validation)
- `db/` — Database access layer (Postgres / Supabase)

## Firewall Contract

Every outbound API response **must** be validated against `packages/stats-schema`
types. The `FantasyDataFilter.validateWebInput()` check runs in middleware before any
data is persisted.

## Status

Phase 1 placeholder — implementation begins in Phase 3.
