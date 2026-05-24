# packages/adapters/

Typed clients for the upstream services in `notbleaux/ZeSporteXte`. Each adapter is thin: types + a transport wrapper + retry/timeout policy. Domain logic does not live here.

## Members

| Package | Wraps | Phase |
|---------|-------|-------|
| `@njz-os/adapters-vaultbrain-client` | `services/vaultbrain` (HTTP + WS) | 1 |
| `@njz-os/adapters-agent-gateway-client` | `services/agent-gateway` (HTTP) | 4 |
| `@njz-os/adapters-api-client` | `services/api` (REST, OpenAPI-generated) | 1 |
| `@njz-os/adapters-identity-client` | identity service (TBD) | 1 |

## Rules

- An adapter may import `@njz-os/core` types only. Never other `@njz-os/*` packages.
- An adapter must surface domain errors as named `Error` subclasses.
- Every call wraps retries + timeouts.
- Tests use `msw` to mock network; never call real upstream in unit tests.

## Contract Surface

The full set of upstream endpoints we depend on is in `contracts/openapi/njz-rat-os.yaml`. To add a new endpoint, follow `ROOT_AXIOMS/03_PROCEDURES/03-add-an-adapter.md`.
