# @njz-os/core

Pure-TypeScript domain types for NJZ RAT-OS. No I/O, no side effects, no framework code.

This is the foundation everything else depends on. Keep it small.

## Surface

- `identity` — `UserId`, `SessionId`, `WorldId` (brand types)
- `progression` — `ModuleSlug`, `StreakState`, `XpTotals`, `ProgressionEvent`, `Reward`

## Adding A Type

1. Add to the appropriate file in `src/`.
2. Register in `.agents/SCHEMA_REGISTRY.md`.
3. Don't add a type that lives more naturally in `@njz-os/<module>`.
