# tests/

This directory holds integration and end-to-end tests for the SATOR platform.

## Subdirectories (planned)

| Directory | Purpose |
|-----------|---------|
| `firewall/` | Verify `FantasyDataFilter` blocks all forbidden fields |
| `api/` | Integration tests for API endpoints |
| `e2e/` | End-to-end tests for the web platform |
| `schema/` | Schema validation tests |

## Existing Game Tests

GDScript determinism tests live in the project root `tests/` node — see
`tests/test_determinism.gd` and `tests/test_determinism.tscn`.

## Running Tests

```bash
# Firewall tests (Phase 3+)
npm run test:firewall

# Schema validation
npm run validate:schema
```

## Status

Phase 1 placeholder — tests implemented alongside library code in Phase 3.
