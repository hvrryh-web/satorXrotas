# SATOR Project Summary

## What is SATOR?

**SATOR** is a three-part esports simulation and analytics platform:

1. **RadiantX** — An offline, deterministic tactical FPS simulation game built with
   Godot 4 and GDScript
2. **Axiom Esports Data** — A tactical FPS analytics pipeline with the SATOR Square
   5-layer visualization (Python + React/D3/WebGL)
3. **SATOR Web** — An online public statistics platform (in development)

A **data partition firewall** separates these components, ensuring game-internal
simulation data never reaches the public web platform.

## RadiantX Game Features

### ✅ Deterministic Simulation
- **20 TPS (Ticks Per Second)** fixed timestep engine
- **Seeded RNG** ensures reproducible matches
- Same seed = same results, always
- Perfect for testing and analysis

### ✅ 5v5 Tactical Gameplay
- 10 autonomous agents (5 per team)
- **Partial observability** - agents only know what they see
- **Belief system** - agent knowledge decays over time
- **Communication delay** simulation (2 ticks)

### ✅ Map System
- **JSON-based maps** with zones and occluders
- Line-of-sight calculations
- Spawn zones and objectives
- Sample map included

### ✅ Tactical Mechanics
- **Smoke grenades** - block vision
- **Flashbangs** - temporarily blind agents
- Vision range and occlusion
- Distance-based accuracy

### ✅ Event Log & Replay
- Records all match events
- **Save/load replays** to JSON
- Full match reconstruction
- Determinism verification

### ✅ Top-Down Viewer
- 2D tactical view
- **Smooth interpolation** (60 FPS rendering from 20 TPS simulation)
- Color-coded teams
- Health bars and status indicators
- Camera controls

### ✅ Playback Controls
- **Play/pause** (Space key)
- **Speed control**: 0.25x, 0.5x, 1x, 2x, 4x
- **Timeline scrubbing** with slider
- Keyboard shortcuts (arrows, +/-)

### ✅ Documentation
- Architecture overview
- Firewall policy
- Project structure guide
- Branch strategy
- Map format specification
- Agent behavior documentation
- Replay system guide
- Quick start guide
- Contributing guidelines
- AI prompting guide

### ✅ Testing & CI
- Determinism tests
- GitHub Actions CI
- JSON validation
- Security checks (CodeQL)

## Project Structure

```
RadiantX/ (SATOR monorepo root)
├── scripts/              # Core game logic (GDScript)
│   ├── MatchEngine.gd    # 20 TPS simulation engine
│   ├── Agent.gd          # Agent with beliefs
│   ├── MapData.gd        # Map loading and LOS
│   ├── EventLog.gd       # Event recording
│   ├── Viewer2D.gd       # Top-down visualization
│   ├── PlaybackController.gd  # Playback controls
│   ├── Main.gd           # Main game controller
│   ├── Data/             # Data types and loading
│   └── Sim/              # Combat resolution subsystem
├── scenes/
│   └── Main.tscn         # Main scene
├── maps/
│   └── training_ground.json  # Sample map
├── Defs/                 # Game definition files (JSON)
│   ├── agents/           # Agent traits and loadouts
│   ├── weapons/          # Weapon stats
│   ├── utilities/        # Grenades and abilities
│   └── rulesets/         # Game rules
├── tests/
│   ├── test_determinism.gd   # Determinism tests
│   └── test_determinism.tscn
├── axiom-esports-data/   # Analytics pipeline
│   ├── analytics/        # SimRating, RAR, guardrails
│   ├── extraction/       # VLR scraping + parsing
│   ├── infrastructure/   # Docker, DB migrations
│   ├── visualization/    # SATOR Square 5-layer viz
│   ├── api/              # FastAPI routes
│   └── docs/             # Data dictionary, architecture
├── packages/
│   ├── stats-schema/     # Public type definitions
│   ├── data-partition-lib/  # Firewall library
│   └── api-client/       # HTTP client
├── apps/
│   ├── radiantx-game/    # Game integration modules
│   └── sator-web/        # Web platform (Phase 3)
├── api/                  # Backend API (Phase 3)
├── docs/
│   ├── FIREWALL_POLICY.md
│   ├── PROJECT_STRUCTURE.md
│   ├── architecture.md
│   └── ...
├── .github/
│   ├── SATOR-COPILOT-PROMPTS.md
│   └── workflows/
│       └── ci.yml        # GitHub Actions CI
├── project.godot         # Godot project file
├── package.json          # npm workspace root
├── README.md
├── LICENSE (MIT)
└── CONTRIBUTING.md
```

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for the full layout.

## Key Technologies

- **Game Engine**: Godot 4.x / GDScript
- **Analytics**: Python 3.11+ (extraction, SimRating, RAR, guardrails)
- **Visualization**: React / TypeScript / D3.js / WebGL (SATOR Square)
- **Database**: PostgreSQL 15 + TimescaleDB (planned)
- **Packages**: TypeScript (stats-schema, data-partition-lib)
- **Platform**: Windows (primary game target), cross-platform compatible
- **Format**: JSON for maps, definitions, and replays
- **CI/CD**: GitHub Actions

## Design Principles

1. **Determinism**: Same input → same output
2. **Offline**: No internet required
3. **Simulation-heavy**: Tactical depth over graphics
4. **Minimal**: Clean, focused implementation
5. **Extensible**: Easy to add features

## Use Cases

- **Tactical Training**: Learn FPS concepts
- **Strategy Testing**: Experiment with tactics
- **Game Development**: Study simulation design
- **AI Research**: Test agent behaviors
- **Education**: Learn about deterministic systems

## Performance

- **CPU Usage**: ~5-10% on modern systems
- **Memory**: ~50-100 MB typical
- **Framerate**: 60 FPS rendering
- **Simulation Rate**: 20 TPS
- **Match Duration**: Unlimited

## Getting Started

1. Install Godot 4.x
2. Clone repository
3. Open `project.godot` in Godot
4. Press F5 to run
5. See [Quick Start Guide](docs/quick_start.md)

## Development Status

### RadiantX Game: ✅ Functional MVP

All core features from the problem statement have been implemented:
- Deterministic 20 TPS engine ✓
- Seeded RNG ✓
- Partial observability ✓
- Belief + comm delay ✓
- Map JSON system ✓
- 5v5 agents ✓
- Smoke/flash mechanics ✓
- Event log ✓
- Replay save/load ✓
- Top-down viewer ✓
- Interpolation ✓
- Play/pause/speed/scrub ✓
- Minimal HUD ✓
- Documentation ✓
- Determinism test ✓
- CI workflow ✓

### Axiom Esports Data: 🟡 Scaffolded

Directory structure, documentation, and module stubs are in place:
- Analytics modules (SimRating, RAR, guardrails) — scaffolded ✓
- Extraction pipeline (scrapers, parsers, bridge) — scaffolded ✓
- Infrastructure (Docker, migrations) — scaffolded ✓
- SATOR Square visualization (5 layers) — Layer 1 implemented, 4 scaffolded ✓
- API routes — scaffolded ✓

### SATOR Web: ⏳ Phase 3 Placeholder

- TypeScript packages (stats-schema, data-partition-lib) — implemented ✓
- Web application — placeholder only

## Axiom Esports Data

The `axiom-esports-data/` directory contains the analytics pipeline:

### Analytics Engine
- **SimRating**: 5-component equal-weight performance metric
- **RAR (Replacement-Adjusted Rating)**: Role-specific replacement levels
- **Investment Grading**: A+ through D player classification
- **Overfitting Guardrails**: Temporal wall, adversarial validation, confidence weighting

### SATOR Square Visualization
A 5-layer palindromic match visualization system:
- **S — Sator Layer**: Hotstreak momentum, pulse animations (D3.js)
- **A — Arepo Layer**: Death stains, clutch crowns
- **T — Tenet Layer**: Area control grading, zone colors
- **O — Opera Layer**: Fog of war (WebGL shader)
- **R — Rotas Layer**: Rotation trails (WebGL vertex shader)

### Extraction Pipeline
- VLR.gg scraping with circuit breaker and rate limiting
- Epoch-based harvesting (historical + incremental)
- Dual-storage protocol (raw immutable + reconstructed calculated)
- SHA-256 integrity checking

See [axiom-esports-data/AXIOM.md](axiom-esports-data/AXIOM.md) for the full specification.

## Future Enhancements

Potential additions:
- More agent AI behaviors
- Additional tactical utilities
- Map editor
- Match statistics
- Network multiplayer
- 3D visualization
- Sound effects

## License

MIT License - See LICENSE file

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines, including the firewall policy and branch strategy.

## Support

- Documentation: `/docs`
- Firewall policy: `docs/FIREWALL_POLICY.md`
- AI prompting guide: `.github/SATOR-COPILOT-PROMPTS.md`
- Issues: GitHub Issues
- Questions: GitHub Discussions

---

**SATOR** — Tactical depth meets deterministic simulation.
