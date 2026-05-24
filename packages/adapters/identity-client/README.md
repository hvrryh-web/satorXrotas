# @njz-os/adapters-identity-client

Thin client for the upstream identity service (TBD). Auth session retrieval, sign-out, tier check.

## Phase 0

Stub returning `null` for `currentSession()` and no-op `signOut()`. Types defined.

## Phase 1

- Passkey + email flows
- HttpOnly cookie session
- Refresh-token rotation
- Tier introspection

Auth model decided via ADR (TBD) before Phase 1 unlocks.
