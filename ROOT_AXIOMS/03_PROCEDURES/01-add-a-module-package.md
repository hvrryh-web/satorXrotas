[Ver001.000]

# PROC-01 — Add a Module Package

1. Confirm an ADR exists for the module surface + lifecycle (`docs/architecture/ADR/ADR-XXXX-<slug>.md`, `Status: Accepted`).
2. Run `pnpm module:new <name>`.
3. The generator creates:
   ```
   packages/@njz-os/<name>/
     package.json
     tsconfig.json
     src/index.ts
     src/types.ts
     test/index.test.ts
     README.md
   ```
4. Edit `package.json`:
   - `name`: `@njz-os/<name>`
   - `version`: `0.0.0` (Phase 0); bumps via release pipeline (Phase 2+).
   - `dependencies` / `peerDependencies`: minimal.
5. Edit `src/index.ts` to define the public surface. Re-export from `src/types.ts` where appropriate.
6. Register canonical types in `.agents/SCHEMA_REGISTRY.md` under the correct section.
7. Add a prototype-system spec: `docs/prototype-systems/PS-XXX-<name>.md` (use template).
8. Add a phase gate row in `.agents/PHASE_GATES.md` if the package is gated by phase.
9. Update `.doc-registry.json` routes if the package answers a documentation query.
10. Open PR. Title: `[packages-engines] add @njz-os/<name>` (or `[packages-ui]` for UI primitives).
