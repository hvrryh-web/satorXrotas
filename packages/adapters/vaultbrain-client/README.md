# @njz-os/adapters-vaultbrain-client

Thin client for the upstream `services/vaultbrain` service in `notbleaux/ZeSporteXte`. WebSocket (live events) + HTTP (CRUD).

## Phase 0 (this commit)

Stub returning `VaultbrainError('NOT_IMPLEMENTED')`. Types defined; transport not wired.

## Phase 1 (G1.vaultbrain-live)

- WS reconnect with exponential backoff
- HTTP retries (3 attempts, exponential backoff)
- Per-event Zod validation
- Token refresh on 401
- Local-first event queue for offline write replay

## Stub Mode for Local Dev

Once implemented, a `dev:stub` script will run a local mimic on `:7100` so frontends can develop without the full upstream.

## Tests

`msw`-mocked unit tests. Integration tests against upstream staging in Phase 1.

## See Also

- ADR-0003 (Vaultbrain as state backend)
- `docs/architecture/INTEGRATION_WITH_ZESPORTEXTE.md`
- `contracts/openapi/njz-rat-os.yaml`
