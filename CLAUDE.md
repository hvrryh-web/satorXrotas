# CLAUDE.md — AI Assistant Guide for RadiantX

## Project Overview

RadiantX is a **deterministic tactical FPS simulation manager** built with **Godot 4** and **GDScript**. It simulates 5v5 tactical matches with a tick-based engine, partial observability, and full replay capability. It is designed for offline Windows play, prioritizing tactical depth and simulation fidelity over graphics.

**Key characteristics:**
- 20 TPS deterministic match engine with seeded RNG
- Top-down 2D visualization with smooth 60 FPS interpolation
- Data-driven combat system with JSON definitions
- Full match recording and replay with playback controls
- MIT licensed

## Repository Structure

```
RadiantX/
├── scripts/                    # Core game logic (GDScript)
│   ├── Main.gd                 # Entry point: HUD, subsystem orchestration
│   ├── MatchEngine.gd          # 20 TPS simulation loop
│   ├── Agent.gd                # Agent AI: beliefs, decisions, vision
│   ├── MapData.gd              # Map loading, LOS calculations
│   ├── EventLog.gd             # Event recording for replays
│   ├── Viewer2D.gd             # Top-down 2D rendering
│   ├── PlaybackController.gd   # Playback modes and speed control
│   ├── Data/                   # Data types and loading (22 files)
│   │   ├── DataTypes.gd        # Enums: TeamSide, Stance, FireMode, etc.
│   │   ├── DataLoader.gd       # Singleton: loads JSON from Defs/
│   │   ├── Agent*.gd           # AgentDef, AgentState, AgentBridge
│   │   ├── Weapon*.gd          # WeaponDef, WeaponState
│   │   ├── Utility*.gd         # UtilityDef, UtilityState
│   │   ├── *Profile.gd         # DamageProfile, SpreadProfile, RecoilProfile, PenetrationProfile
│   │   ├── SimEvent.gd         # Match event types
│   │   ├── MatchConfig.gd      # Match configuration
│   │   └── ...                 # EffectSpec, RulesetDef, TraitBlock, etc.
│   └── Sim/                    # Combat resolution subsystem (6 files)
│       ├── CombatResolver.gd   # Integration layer for combat
│       ├── DuelResolver.gd     # LOD-based duel resolution (HIGH/MEDIUM/LOW)
│       ├── DuelContext.gd      # Context for a duel
│       ├── DuelResult.gd       # Result of a duel
│       ├── RaycastDuelEngine.gd # Detailed per-shot raycast combat
│       └── TTKDuelEngine.gd    # Fast TTK approximation
├── scenes/
│   └── Main.tscn               # Main scene (instantiates Main.gd)
├── maps/
│   └── training_ground.json    # Sample 100x100 training map
├── Defs/                       # Game definition files (JSON)
│   ├── agents/agents.json      # Agent traits and loadouts
│   ├── weapons/weapons.json    # Weapon stats (damage, recoil, spread)
│   ├── utilities/              # cs_grenades.json, val_abilities.json
│   └── rulesets/rulesets.json  # Game rules configuration
├── tests/
│   ├── test_determinism.gd     # Determinism verification tests
│   └── test_determinism.tscn   # Test scene
├── docs/                       # Documentation (10+ files)
│   ├── architecture.md         # System design overview
│   ├── agents.md               # Agent behavior documentation
│   ├── map_format.md           # JSON map specification
│   ├── replay.md               # Replay system guide
│   ├── quick_start.md          # Getting started guide
│   ├── custom-agents.md        # Custom AI agent setup
│   └── ...                     # Reviews and assessments
├── tactical-fps-sim-core-updated/  # Reference C# implementation (not used at runtime)
├── project.godot               # Godot 4 project config
├── README.md
├── PROJECT_SUMMARY.md
├── CONTRIBUTING.md
└── LICENSE                     # MIT
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Engine | Godot 4.0+ |
| Language | GDScript |
| Data format | JSON (maps, definitions, replays) |
| CI | GitHub Actions (structural validation) |
| Platform target | Windows primary, cross-platform capable |

**No external dependencies.** Everything uses Godot built-in classes.

## Architecture

### Simulation Pipeline (per tick)

```
MatchEngine._physics_process()
  → Update agent beliefs (partial observability)
  → Agent decision-making (per agent)
  → Apply actions (movement, firing)
  → Process tactical events (smoke, flash)
  → CombatResolver → DuelResolver → Raycast/TTK engines
  → Check win conditions
  → EventLog.record()
```

### Key Constants

| Constant | Value | Location |
|----------|-------|----------|
| Physics ticks | 20 TPS | project.godot |
| Tick interval | 50ms | MatchEngine.gd |
| Vision range | 50 units | Agent.gd |
| Smoke duration | 300 ticks (15s) | Agent.gd |
| Fire rate | 4 ticks (5 shots/s) | Agent.gd |
| Communication delay | 2 ticks | Agent.gd |
| Flash radius | 20 units | MatchEngine.gd |
| Max events | 100,000 per match | EventLog.gd |

### Signal Flow

- `MatchEngine` emits: `tick_processed`, `match_started`, `match_ended`, `round_ended`
- `PlaybackController` emits: `playback_state_changed`, `speed_changed`, `tick_changed`
- `Main.gd` listens to all signals and updates the HUD

### Combat LOD System

`DuelResolver` selects engine based on level of detail:
- **HIGH** — `RaycastDuelEngine`: per-shot LOS raycasts, full ballistics
- **MEDIUM** — Raycast with simplified calculations
- **LOW** — `TTKDuelEngine`: fast time-to-kill approximation

## Coding Conventions

### Naming

- **Variables/functions:** `snake_case` — `agent_health`, `calculate_damage()`
- **Classes:** `PascalCase` — `MatchEngine`, `AgentDef`
- **Constants:** `UPPER_SNAKE_CASE` — `TICKS_PER_SECOND`
- **Enums:** `PascalCase` — `TeamSide`, `FireMode`
- **Private members:** leading underscore — `_process_combat()`, `_has_line_of_sight()`

### Indentation

**Tabs** (not spaces) — this is GDScript/Godot convention.

### File Organization

- One class per file
- Use `class_name ClassName` at the top for Godot auto-registration
- Use `extends NodeType` for inheritance
- Related classes grouped in subdirectories (`Data/`, `Sim/`)

### Patterns

- **Signals** for decoupled communication (Observer pattern)
- **Data-driven design**: JSON definitions in `Defs/`, loaded by `DataLoader` singleton
- **State separation**: `*Def` classes for static definitions, `*State` classes for runtime state
- **Bridge pattern**: `AgentBridge` connects legacy Agent data to the combat subsystem

## Determinism Rules (Critical)

All simulation logic **must** be deterministic. When modifying game logic:

1. **Only use seeded RNG** — always go through the `RandomNumberGenerator` instance with a set seed
2. **Fixed timestep** — 20 TPS, 50ms per tick; never use delta-time in simulation logic
3. **Consistent ordering** — process agents/actions in the same order every tick
4. **No floating point accumulation** in critical paths
5. **Verify with tests** — run `tests/test_determinism.tscn` (same seed must produce identical event logs)

## Testing

### Running Tests

Open `tests/test_determinism.tscn` in Godot Editor, right-click, and select "Run This Scene." Check the console for "All determinism tests passed!"

### Test Coverage

- `test_same_seed_same_results()` — identical seed produces identical event logs
- `test_different_seed_different_results()` — different seeds diverge
- `test_replay_consistency()` — saved replays load and match originals

### Manual Testing Checklist

1. Run a full match and observe the 2D viewer
2. Save a replay, load it, verify it matches
3. Test with different seeds
4. Verify playback controls (play/pause, speed, scrubbing)

## CI Pipeline

**File:** `.github/workflows/ci.yml`
**Triggers:** push to `main`/`develop`, PR to `main`

The CI validates:
1. Project structure — `project.godot`, `scripts/`, `maps/`, `docs/`, `tests/` exist
2. JSON validity — all `maps/*.json` files parse correctly
3. GDScript presence — `.gd` files exist under `scripts/`
4. Documentation — `README.md`, `docs/architecture.md`, `docs/map_format.md`, `docs/agents.md`, `docs/replay.md`
5. License — MIT License present

**Note:** CI does not run Godot or execute game tests. It performs structural validation only.

## How to Run

1. Install [Godot 4.0+](https://godotengine.org/download)
2. Open `project.godot` in Godot Editor
3. Press F5 or click Play to run `scenes/Main.tscn`

### Keyboard Controls

| Key | Action |
|-----|--------|
| Space | Play/Pause |
| `+` / `-` | Speed up / slow down |
| Left/Right arrows | Scrub backward/forward (20 ticks) |

## Working with Game Data

### Maps (`maps/*.json`)

```json
{
  "name": "Map Name",
  "width": 100, "height": 100,
  "zones": [{"id": "spawn_a", "x": 10, "y": 10, "width": 15, "height": 15}],
  "occluders": [{"x": 45, "y": 20, "width": 10, "height": 30}]
}
```

### Definitions (`Defs/`)

- `agents/agents.json` — agent traits, HP, armor, loadout references
- `weapons/weapons.json` — fire modes, magazine size, RPM, damage/spread/recoil/penetration profiles
- `utilities/` — CS-style grenades and VAL-style abilities
- `rulesets/rulesets.json` — game mode configuration

All loaded at runtime by `DataLoader.gd` (singleton). Access via `DataLoader.get_agent()`, `get_weapon()`, etc.

### Replays

Saved to user data directory as `replay_TIMESTAMP.json`. Contains tick-timestamped events for full match reconstruction.

## Documentation Index

| File | Purpose |
|------|---------|
| `README.md` | User-facing overview and quick start |
| `PROJECT_SUMMARY.md` | High-level project summary |
| `CONTRIBUTING.md` | Contribution guidelines and coding standards |
| `docs/architecture.md` | System design and data flow |
| `docs/agents.md` | Agent AI, beliefs, partial observability |
| `docs/map_format.md` | JSON map specification |
| `docs/replay.md` | Replay save/load and verification |
| `docs/quick_start.md` | Getting started guide |
| `docs/custom-agents.md` | Custom AI agent setup |
| `docs/combat_system_review.md` | Combat mechanics deep-dive |
| `docs/backend_architecture_review.md` | Backend architecture analysis |
| `docs/UI_UX_ACCESSIBILITY_ASSESSMENT.md` | Accessibility audit |

## Common Tasks for AI Assistants

### Adding a new weapon

1. Add definition to `Defs/weapons/weapons.json`
2. Include damage, spread, recoil, and penetration profile objects
3. Reference the weapon ID in an agent's `loadoutWeaponIds` array in `agents.json`
4. `DataLoader` picks it up automatically

### Adding a new utility/grenade

1. Add definition to `Defs/utilities/cs_grenades.json` or `val_abilities.json`
2. Define cast type, effects, throw ballistics
3. Reference in agent loadouts
4. If new `EffectKind` is needed, add to `DataTypes.gd` enum and handle in `MatchEngine.gd`

### Adding a new map

1. Create a new `.json` file in `maps/`
2. Follow the schema in `docs/map_format.md`
3. Include spawn zones for both teams and occluders
4. Update `Main.gd` to load the new map (currently hardcoded path)

### Modifying agent AI

1. Edit `Agent.gd` — belief updates, decision logic, state transitions
2. Maintain determinism: use only the seeded RNG, avoid nondeterministic operations
3. Run determinism tests after changes

### Modifying combat resolution

1. Edit files in `scripts/Sim/`
2. `CombatResolver.gd` is the entry point from `MatchEngine`
3. `DuelResolver.gd` dispatches to `RaycastDuelEngine` or `TTKDuelEngine`
4. All combat data flows through `DuelContext` and returns `DuelResult`
