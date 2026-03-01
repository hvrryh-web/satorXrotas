# apps/radiantx-game/src/

This directory is reserved for new game-side modules introduced in Phase 2+.

## Planned Contents

- `LiveSeasonModule.gd` — Extracts and sanitizes match statistics for the SATOR web
  platform. This module is the **primary enforcement point** for the data partition
  firewall: it calls `FantasyDataFilter.sanitizeForWeb()` before any data leaves the
  game boundary.

## Rules

- All GDScript files in this directory **must not** expose `GAME_ONLY_FIELDS` to the
  API layer (see `docs/FIREWALL_POLICY.md`).
- Unit tests for new modules belong in `tests/`.

## Status

Phase 1 placeholder — implementation begins in Phase 2.
