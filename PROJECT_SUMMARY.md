# SATOR Project Summary

## What is SATOR?

**SATOR** is a two-part esports simulation platform:

1. **RadiantX** — An offline, deterministic tactical FPS simulation game built with
   Godot 4 and GDScript
2. **SATOR Web** — An online public statistics platform (in development)

A **data partition firewall** separates these two components, ensuring game-internal
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
│   └── Main.gd           # Main game controller
├── scenes/
│   └── Main.tscn         # Main scene
├── maps/
│   └── training_ground.json  # Sample map
├── tests/
│   ├── test_determinism.gd   # Determinism tests
│   └── test_determinism.tscn
├── packages/
│   ├── stats-schema/     # Public type definitions
│   └── data-partition-lib/  # Firewall library
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

- **Engine**: Godot 4.x
- **Language**: GDScript
- **Platform**: Windows (primary), cross-platform compatible
- **Format**: JSON for maps and replays
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

✅ **Complete and Ready**

All features from the problem statement have been implemented:
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

## Future Enhancements

Potential additions (not in scope):
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
