# @njz-os/adapters-api-client

Thin client for upstream `services/api`. OpenAPI-generated in Phase 1+; manual `health()` stub for Phase 0.

## Generation (Phase 1+)

```bash
pnpm --filter @njz-os/adapters-api-client generate
# Reads contracts/openapi/njz-rat-os.yaml; writes src/generated/
```

## Convention

- Never hand-edit `src/generated/`.
- Wrap generated methods in `src/wrappers/<feature>.ts` for retry/timeout policy.
- Public surface re-exported from `src/index.ts`.

## Errors

`ApiError` carries the HTTP status. Caller decides retry strategy.
