# SATOR — Esports Simulation Platform

**SATOR** is a two-part esports simulation platform:

1. **RadiantX** — An offline, deterministic tactical FPS simulation game built with Godot 4 and GDScript
2. **SATOR Web** — An online public statistics platform (in development)

A data partition **firewall** ensures game-internal simulation data never reaches the public web platform.

## RadiantX Game Features

- **Deterministic 20 TPS Match Engine**: Seeded RNG for reproducible matches
- **5v5 Tactical Gameplay**: Full team simulation with AI agents
- **Partial Observability**: Belief systems and communication delay simulation
- **Map System**: JSON-based maps with zones and occluders
- **Tactical Mechanics**: Smoke grenades, flashbangs, vision occlusion
- **Event Log & Replay**: Full match recording with save/load
- **Top-Down Viewer**: Smooth interpolated 2D visualization
- **Playback Controls**: Play/pause, speed control, timeline scrubbing
- **Determinism Verification**: Built-in tests to ensure consistency

## Requirements

- Godot 4.0 or higher (game)
- Node.js 20+ (TypeScript packages, Phase 3+)
- Windows (primary game target platform)

## Quick Start

### Playing RadiantX (Offline Game)

1. Install Godot 4.x from [godotengine.org](https://godotengine.org/)
2. Clone this repository
3. Open `project.godot` in Godot
4. Press F5 to run

See the [Quick Start Guide](docs/quick_start.md) for detailed instructions.

### Running TypeScript Packages

```bash
npm install        # Install dependencies
npm run build      # Build all packages
npm run validate:schema  # Validate public stats schema
npm run test:firewall    # Run firewall enforcement tests
```

## Architecture

SATOR uses a two-layer architecture with a strict data partition firewall:

```
Game Simulation (Godot / GDScript)
        │
        ▼
FantasyDataFilter.sanitizeForWeb()   ◄── Firewall
        │
        ▼
API Layer → SATOR Web Platform
```

See [docs/ARCHITECTURE.md](docs/architecture.md) for the full architecture overview and
[docs/FIREWALL_POLICY.md](docs/FIREWALL_POLICY.md) for the data partition rules.

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/architecture.md](docs/architecture.md) | System architecture overview |
| [docs/FIREWALL_POLICY.md](docs/FIREWALL_POLICY.md) | ★ Data partition firewall policy |
| [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) | Repository structure guide |
| [docs/BRANCH_STRATEGY.md](docs/BRANCH_STRATEGY.md) | Git branch strategy |
| [docs/map_format.md](docs/map_format.md) | Map JSON specification |
| [docs/agents.md](docs/agents.md) | Agent AI behavior |
| [docs/replay.md](docs/replay.md) | Replay system guide |
| [docs/quick_start.md](docs/quick_start.md) | Getting started guide |
| [docs/custom-agents.md](docs/custom-agents.md) | AI agent configuration |
| [.github/SATOR-COPILOT-PROMPTS.md](.github/SATOR-COPILOT-PROMPTS.md) | AI-assisted development guide |

## Map Format

```json
{
  "name": "Example Map",
  "width": 100,
  "height": 100,
  "zones": [
    {"id": "spawn_a", "x": 10, "y": 10, "width": 20, "height": 20},
    {"id": "spawn_b", "x": 70, "y": 70, "width": 20, "height": 20}
  ],
  "occluders": [
    {"x": 45, "y": 30, "width": 10, "height": 40}
  ]
}
```

See `maps/` for examples and [docs/map_format.md](docs/map_format.md) for the full specification.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines, including the firewall policy and branch strategy.

## License

MIT License — See LICENSE file for details.
