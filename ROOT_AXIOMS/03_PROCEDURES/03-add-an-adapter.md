[Ver001.000]

# PROC-03 — Add or Update an Adapter

Adapters are how RAT-OS talks to ZeSporteXte services. They live in `packages/adapters/<service>-client/`. They are thin: a typed surface + retries/timeouts + nothing else.

## To add a new method

1. Confirm the upstream endpoint exists in `notbleaux/ZeSporteXte` (check `services/<service>/` or its OpenAPI spec). If not, file an issue there first and pause this work.
2. Update `contracts/openapi/njz-rat-os.yaml` (or `contracts/events/*.json` for an event) to describe the dependency.
3. If `api-client`, regenerate the typed client:
   ```bash
   pnpm --filter @njz-os/adapters-api-client generate
   ```
   The output lives in `packages/adapters/api-client/src/generated/` — never hand-edit.
4. Add a thin wrapper method in the adapter package that:
   - Validates arguments with `zod` if user-supplied.
   - Wraps the call with a retry policy (default: 3 retries, exponential backoff).
   - Surfaces domain errors as `Error` subclasses (`VaultbrainError`, `AgentGatewayError`, etc.).
5. Add a unit test mocking the network with `msw`.
6. Update `.agents/SCHEMA_REGISTRY.md` if any new type was introduced.
7. PR title: `[adapters] expose <feature> from <service>`.

## To bump a contract version

1. Update the version in `contracts/openapi/njz-rat-os.yaml`.
2. Regenerate.
3. Update the adapter consumers to match the new shape.
4. ADR if the change is breaking.
5. Test all affected apps before merging.
