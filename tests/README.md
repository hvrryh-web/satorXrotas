# tests/

Cross-package and cross-app tests that don't belong inside a single package.

```
e2e/           Playwright end-to-end (Phase 1+)
integration/   Cross-package integration (adapter + module pairs)
```

Package-local unit tests live under `packages/<name>/test/` or alongside source as `<name>.test.ts`.
