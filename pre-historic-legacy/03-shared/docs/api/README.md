# docs/api/

Placeholder for SATOR API documentation.

## Planned Contents

- `endpoints.md` — REST API reference
- `authentication.md` — Auth strategy
- `firewall-middleware.md` — How the API enforces data partition
- `schemas.md` — Request / response schema reference

## Firewall Note

All response schemas documented here must conform to `packages/stats-schema` types.
No `GAME_ONLY_FIELDS` (see `docs/FIREWALL_POLICY.md`) may appear in any API response
example.

## Status

Phase 1 placeholder — documentation written in Phase 3.
