# SATOR — Esports Simulation Platform

**SATOR** is a three-part esports simulation and analytics platform:

1. **RadiantX** — An offline, deterministic tactical FPS simulation game built with Godot 4 and GDScript
2. **Axiom Esports Data** — A tactical FPS analytics pipeline with the SATOR Square 5-layer visualization
3. **SATOR Web** — An online public statistics platform (in development)

A data partition **firewall** ensures game-internal simulation data never reaches the public web platform.

## Components

### RadiantX Game (Offline)

- **Deterministic 20 TPS Match Engine**: Seeded RNG for reproducible matches
- **5v5 Tactical Gameplay**: Full team simulation with AI agents
- **Dual Combat Engines**: Raycast (high fidelity) + TTK (Monte Carlo) LOD system
- **Partial Observability**: Belief systems and communication delay simulation
- **Map System**: JSON-based maps with zones and occluders
- **Tactical Mechanics**: Smoke grenades, flashbangs, vision occlusion
- **Event Log & Replay**: Full match recording with save/load
- **Top-Down Viewer**: Smooth interpolated 2D visualization
- **Playback Controls**: Play/pause, speed control, timeline scrubbing
- **Determinism Verification**: Built-in tests to ensure consistency

### Axiom Esports Data (Analytics)

- **37-field KCRITR Schema**: Comprehensive player performance database
- **SATOR Square Visualization**: 5-layer palindromic match analysis (D3.js + WebGL)
- **SimRating & RAR Metrics**: Role-adjusted performance analytics
- **Investment Grading**: A+ through D player classification
- **Overfitting Guardrails**: Temporal wall, adversarial validation, confidence weighting
- **Extraction Pipeline**: VLR.gg scraping with dual-storage protocol

### SATOR Web (Public Stats)

- Phase 3+ — displays only firewall-sanitized public statistics

## Requirements

- Godot 4.0+ (game)
- Docker + Docker Compose (Axiom database)
- Python 3.11+ (analytics pipeline)
- Node.js 20+ (TypeScript packages, web platform)

## Quick Start

### Playing RadiantX

```bash
# Install Godot 4.x from godotengine.org
git clone https://github.com/hvrryh-web/RadiantX.git
cd RadiantX
# Open project.godot in Godot, press F5
```

See the [Quick Start Guide](docs/quick_start.md) for detailed instructions.

### Running Axiom Analytics

```bash
cd axiom-esports-data
docker-compose -f infrastructure/docker-compose.yml up -d
cd extraction && pip install -r requirements.txt
python src/scrapers/epoch_harvester.py --mode=delta
```

### Running TypeScript Packages

```bash
npm install
npm run build
npm run validate:schema
npm run test:firewall
```

## Architecture

SATOR uses a three-layer architecture with a strict data partition firewall:

```
Game Simulation (Godot / GDScript)
        │
        ├──→ EventLog → Extraction Bridge → Axiom Analytics (Python)
        │                                        │
        │                                        ▼
        │                                  SATOR Square Viz (React/D3/WebGL)
        │
        ▼
FantasyDataFilter.sanitizeForWeb()   ◄── Firewall
        │
        ▼
API Layer → SATOR Web Platform
```

See [docs/architecture.md](docs/architecture.md) for the game system design.
See [axiom-esports-data/AXIOM.md](axiom-esports-data/AXIOM.md) for the analytics pipeline.
See [docs/FIREWALL_POLICY.md](docs/FIREWALL_POLICY.md) for data partition rules.

## Documentation

| Document | Purpose |
|----------|---------|
| [Quick Start](docs/quick_start.md) | Getting started guide |
| [Architecture](docs/architecture.md) | System design overview |
| [Agent Behavior](docs/agents.md) | AI agent documentation |
| [Map Format](docs/map_format.md) | JSON map specification |
| [Replay System](docs/replay.md) | Match replay guide |
| [Firewall Policy](docs/FIREWALL_POLICY.md) | Data partition rules |
| [SATOR Architecture](axiom-esports-data/docs/SATOR_ARCHITECTURE.md) | 5-layer visualization spec |
| [Data Dictionary](axiom-esports-data/docs/DATA_DICTIONARY.md) | 37-field KCRITR schema |
| [Custom Agents](docs/custom-agents.md) | AI agent setup for development |
| [Contributing](CONTRIBUTING.md) | Contribution guidelines |

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

- **RadiantX Game**: [MIT License](LICENSE)
- **Axiom Esports Data**: [CC BY-NC 4.0](axiom-esports-data/LICENSE)
