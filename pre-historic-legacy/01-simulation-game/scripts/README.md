# scripts/

This directory contains the core GDScript game logic for RadiantX.

## Game Scripts

| File | Purpose |
|------|---------|
| `Main.gd` | Entry point: HUD and subsystem orchestration |
| `MatchEngine.gd` | 20 TPS deterministic simulation loop |
| `Agent.gd` | Agent AI: beliefs, decisions, vision |
| `MapData.gd` | Map loading and LOS calculations |
| `EventLog.gd` | Event recording for replays |
| `Viewer2D.gd` | Top-down 2D rendering |
| `PlaybackController.gd` | Playback modes and speed control |
| `Data/` | Data types and loading (22 files) |
| `Sim/` | Combat resolution subsystem (6 files) |

## Build Automation Scripts

Shell scripts for CI/CD automation live in the root `build-scripts/` directory
(created in Phase 3). They are invoked via the root `package.json` scripts section.

## Coding Rules

All GDScript in this directory must:
- Use tabs for indentation (not spaces)
- Use `snake_case` for variables/functions, `PascalCase` for classes
- Maintain determinism: only seeded RNG, fixed 50ms tick, consistent ordering
- Emit signals for inter-system communication

See `CONTRIBUTING.md` and `docs/architecture.md` for full conventions.
