# MOVED — Frozen Game Material Relocated to ESPORTEZ-MANAGER

The Godot 4 tactical FPS simulation project (previous identity: **Tact FPS
Simulation Game**) that lived here has been moved to
[`notbleaux/ESPORTEZ-MANAGER`](https://github.com/notbleaux/ESPORTEZ-MANAGER).

## Status

**FROZEN / DEFERRED.** This material is preserved for reference only at the
new location. Do not continue, finish, redesign, or evaluate this work as part
of routine satorXrotas activity. satorXrotas is being kept as archive / ad hoc
storage only.

## Source (here, satorXrotas)

- **Path that previously existed here:** `pre-historic-legacy/01-simulation-game/`
- **Source commit at time of move:** `05616d3ece510136a881eda23354c0ee7026e87d`
- **Source branch:** `main`

## Destination

- **Repository:** https://github.com/notbleaux/ESPORTEZ-MANAGER
- **Path:** `imported/satorxrotas/frozen-game-material/01-simulation-game/`
- **Companion manifest at destination:** `imported/satorxrotas/MANIFEST.md`
- **Companion import PR:** https://github.com/notbleaux/ESPORTEZ-MANAGER/pull/1

## Transfer

- **Transfer date (UTC):** 2026-05-11
- **Purpose:** Move frozen game-development material out of the satorXrotas
  active tree so satorXrotas can be repurposed as archive / ad hoc storage
  only. ESPORTEZ-MANAGER becomes the canonical historical record alongside
  its existing Godot project.
- **Method:** PR-only migration (no force pushes, no direct main commits, no
  destructive default-branch deletion).

## What was moved

The entire `pre-historic-legacy/01-simulation-game/` subtree, including:

- `Defs/` (agents, rulesets, utilities, weapons JSON)
- `maps/training_ground.json`
- `scenes/Main.tscn`
- `scripts/` (`Agent.gd`, `EventLog.gd`, `Main.gd`, `MapData.gd`,
  `MatchEngine.gd`, `PlaybackController.gd`, `Viewer2D.gd`, `Data/`, `Sim/`)
- `tactical-fps-sim-core-updated/` (`SimCore/`, `SchemasTS/`, `ConsoleRunner/`,
  `SimConsoleRunner/`, `tools/`, solution files)
- `tests/` (`test_determinism.gd`, `test_determinism.tscn`, `README.md`)
- `project.godot`, `icon.svg`

## What was NOT moved (and is preserved here)

All other `pre-historic-legacy/` contents remain in place:

- `pre-historic-legacy/02-website/` — marketing website archive
- `pre-historic-legacy/03-shared/` — monorepo shared packages
- `pre-historic-legacy/04-tests/` — integration tests
- `pre-historic-legacy/05-legacy-docs/` — historical documentation
- `pre-historic-legacy/ARCHIVE-MANIFEST.md`, `MIGRATION-PLAN.md`,
  `REVIEW-SCHEDULE.md`

Any archive / ad hoc storage material elsewhere in the repository (including
the `archives/njzetao5-transfer` material, if present) is intentionally
**untouched** by this move.

## How to use this pointer

If you are looking for the game-development source files that used to be at
`pre-historic-legacy/01-simulation-game/<something>`, go to:

```
https://github.com/notbleaux/ESPORTEZ-MANAGER
  → imported/satorxrotas/frozen-game-material/01-simulation-game/<something>
```

This file is the only artifact that remains in this directory. Do not add
further files here; if game material needs to be revived, that decision and
work belong in ESPORTEZ-MANAGER, not here.
