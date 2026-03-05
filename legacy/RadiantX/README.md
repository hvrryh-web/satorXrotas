# RadiantX - Tactical FPS Coach Simulator (LEGACY)

**Status:** LEGACY ARCHIVE  
**Archived Date:** March 5, 2026  
**Original Repository:** RadiantX  
**Current Repository:** satorXrotas  
**Relationship:** This is the original Godot 4 simulation game code, preserved as part of the SATOR platform evolution.

---

## ⚠️ Legacy Notice

This folder contains the **original RadiantX codebase** as it existed before the migration to satorXrotas and subsequent evolution into the SATOR platform.

**What is RadiantX?**
RadiantX was the original name for the deterministic tactical FPS simulation game. It has since evolved into:
- **satorXrotas** - The intermediate evolution
- **SATOR / eSports-EXE** - The current comprehensive esports platform

---

## Original Description

A deterministic, simulation-heavy tactical FPS manager for offline Windows play, built with Godot 4 and GDScript.

### Original Features

- **Deterministic 20 TPS Match Engine**: Seeded RNG for reproducible matches
- **5v5 Tactical Gameplay**: Full team simulation with AI agents
- **Partial Observability**: Belief systems and communication delay simulation
- **Map System**: JSON-based maps with zones and occluders
- **Tactical Mechanics**: Smoke grenades, flashbangs, vision occlusion
- **Event Log & Replay**: Full match recording with save/load
- **Top-Down Viewer**: Smooth interpolated 2D visualization
- **Playback Controls**: Play/pause, speed control, timeline scrubbing
- **Determinism Verification**: Built-in tests to ensure consistency

---

## Historical Context

### Evolution Timeline

1. **RadiantX** (Original) → Godot 4 tactical FPS simulation
2. **satorXrotas** (Evolution) → Expanded with web platform and data pipeline
3. **SATOR / eSports-EXE** (Current) → Full esports analytics ecosystem

### What Changed

| Aspect | RadiantX (Legacy) | SATOR (Current) |
|--------|------------------|-----------------|
| Scope | Godot game only | Full platform (game + web + data) |
| Name | RadiantX | SATOR-eXe-ROTAS |
| Repository | hvrryh-web/satorXrotas | notbleaux/eSports-EXE |
| Components | Game only | Game + Website + Pipeline + API |

---

## Requirements

- Godot 4.0 or higher
- Windows (primary target platform)

## Getting Started (Historical)

### Opening the Project

1. Install Godot 4.x from [godotengine.org](https://godotengine.org/)
2. Navigate to this `legacy/RadiantX` directory
3. Open the project in Godot by selecting the `project.godot` file

### Running a Match

1. Run the main scene (F5)
2. Use the playback controls to play/pause, adjust speed, or scrub through the timeline
3. Watch the top-down tactical view of the 5v5 match

---

## Architecture

### Core Components

- **MatchEngine**: Handles tick-based simulation at 20 TPS with deterministic RNG
- **Agent**: Individual player entity with beliefs and communication
- **MapData**: Loads and manages map geometry and zones
- **EventLog**: Records all events for replay functionality
- **Viewer2D**: Top-down visualization with interpolation
- **PlaybackController**: Manages playback controls and timeline

### Determinism

The engine uses seeded random number generation to ensure matches are reproducible:
- Same seed + same inputs = same results
- Replays can be verified by re-running with the same seed
- Automated tests verify determinism

---

## Documentation (Historical)

- [Architecture Overview](docs/architecture.md)
- [Map Format Specification](docs/map_format.md)
- [Agent Behavior](docs/agents.md)
- [Replay System](docs/replay.md)
- [Custom AI Agents](docs/custom-agents.md)

---

## License

MIT License - See LICENSE file for details

## Contributing (Historical)

This is preserved legacy code. For current development, see the main satorXrotas repository.

---

**RadiantX** - The foundation of the SATOR platform.  
*Preserved for historical reference and educational purposes.*
