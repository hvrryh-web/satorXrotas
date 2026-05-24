# tests/integration/

Cross-package integration tests.

## Targets

- Adapter + module pairs: focus-engine emits a session.complete event → vaultbrain-client receives it correctly.
- Progression reducer + analytics scoring against canned event logs.
- Contract validation: actual upstream responses (in staging) match `contracts/openapi/njz-rat-os.yaml`.

Phase 1+.
