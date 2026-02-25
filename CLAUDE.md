# CLAUDE.md — AI Assistant Guide for RadiantX

## Project Overview

**SATOR** is a three-part esports simulation and analytics platform. The repository is a monorepo containing:

1. **RadiantX** — A deterministic tactical FPS simulation manager built with **Godot 4** and **GDScript**. It simulates 5v5 tactical matches with a tick-based engine, partial observability, and full replay capability.
2. **Axiom Esports Data** — A tactical FPS analytics pipeline with the SATOR Square 5-layer visualization, built with **Python** (analytics) and **React/TypeScript/D3/WebGL** (visualization).
3. **SATOR Web** — An online public statistics platform (in development), with **TypeScript** packages for data partitioning and schema validation.

**Key characteristics:**
- 20 TPS deterministic match engine with seeded RNG
- Top-down 2D visualization with smooth 60 FPS interpolation
- Data-driven combat system with JSON definitions
- Full match recording and replay with playback controls
- 37-field KCRITR analytics schema with SimRating and RAR metrics
- SATOR Square 5-layer palindromic match visualization
- Data partition firewall between game internals and public web
- MIT licensed (game), CC BY-NC 4.0 (analytics)

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
├── axiom-esports-data/         # Analytics pipeline (Python + React/TS)
│   ├── AXIOM.md                # AI agent operational guide
│   ├── analytics/              # SimRating, RAR, guardrails, investment grading
│   │   ├── simrating/          # 5-component performance metric
│   │   ├── rar/                # Role-adjusted replacement rating
│   │   ├── investment/         # A+ through D grading
│   │   ├── guardrails/         # Temporal wall, overfitting guard
│   │   └── temporal/           # Age curves, decay weights
│   ├── extraction/             # VLR scraping and data parsing
│   │   ├── scrapers/           # vlr_resilient_client, epoch_harvester
│   │   ├── parsers/            # match_parser, role_classifier, economy_inference
│   │   ├── bridge/             # extraction_bridge (EventLog → spatial_events)
│   │   └── storage/            # raw_repository, reconstruction_repo, integrity_checker
│   ├── infrastructure/         # Docker, database migrations
│   │   ├── docker-compose.yml  # Postgres 15 + TimescaleDB + Redis
│   │   ├── migrations/         # 4 SQL migration files
│   │   └── seed_data/          # Role baselines, ground truth
│   ├── visualization/          # SATOR Square 5-layer viz (React/D3/WebGL)
│   │   ├── sator-square/       # SatorLayer, ArepoLayer, TenetLayer, OperaLayer, RotasLayer
│   │   ├── hooks/              # useSpatialData.ts
│   │   └── shaders/            # fog.frag, dust.vert
│   ├── api/                    # FastAPI routes
│   └── docs/                   # Data dictionary, architecture, epochs
├── packages/                   # TypeScript shared packages
│   ├── stats-schema/           # Public field type definitions
│   ├── data-partition-lib/     # FantasyDataFilter firewall enforcement
│   └── api-client/             # HTTP client (planned)
├── apps/
│   ├── radiantx-game/          # Game integration modules
│   └── sator-web/              # Web platform (Phase 3)
├── api/                        # Backend API (Phase 3)
├── docs/                       # Documentation (10+ files)
│   ├── architecture.md         # System design overview
│   ├── agents.md               # Agent behavior documentation
│   ├── map_format.md           # JSON map specification
│   ├── replay.md               # Replay system guide
│   ├── quick_start.md          # Getting started guide
│   ├── custom-agents.md        # Custom AI agent setup
│   ├── FIREWALL_POLICY.md      # Data partition rules
│   ├── combat_system_review.md # Combat mechanics deep-dive
│   └── ...                     # Reviews and assessments
├── tactical-fps-sim-core-updated/  # Reference C# implementation (not used at runtime)
├── project.godot               # Godot 4 project config
├── package.json                # npm workspace root
├── README.md
├── PROJECT_SUMMARY.md
├── CONTRIBUTING.md
└── LICENSE                     # MIT
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Game Engine | Godot 4.0+ / GDScript |
| Analytics | Python 3.11+ |
| Visualization | React / TypeScript / D3.js / WebGL |
| Database | PostgreSQL 15 + TimescaleDB (planned) |
| Packages | TypeScript (stats-schema, data-partition-lib) |
| Data format | JSON (maps, definitions, replays) |
| CI | GitHub Actions (structural validation) |
| Platform target | Windows primary, cross-platform capable |

**Game dependencies:** None — uses Godot built-in classes only.
**Analytics dependencies:** See `axiom-esports-data/extraction/requirements.txt`.

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
| `docs/FIREWALL_POLICY.md` | Data partition firewall rules |
| `docs/combat_system_review.md` | Combat mechanics deep-dive |
| `docs/backend_architecture_review.md` | Backend architecture analysis |
| `docs/UI_UX_ACCESSIBILITY_ASSESSMENT.md` | Accessibility audit |
| `axiom-esports-data/AXIOM.md` | Analytics pipeline operational guide |
| `axiom-esports-data/docs/SATOR_ARCHITECTURE.md` | 5-layer visualization spec |
| `axiom-esports-data/docs/DATA_DICTIONARY.md` | 37-field KCRITR schema |
| `axiom-esports-data/docs/CONFIDENCE_TIERS.md` | Data confidence classification |
| `axiom-esports-data/docs/EXTRACTION_EPOCHS.md` | Extraction epoch definitions |

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

## Working with Axiom Esports Data

### Directory: `axiom-esports-data/`

This is the analytics pipeline. It has its own `AXIOM.md` for detailed operational guidance.

### Analytics Modules (`analytics/`)

- `simrating/calculator.py` — 5-component equal-weight SimRating metric
- `simrating/normalizer.py` — Z-score normalization by season
- `rar/decomposer.py` + `replacement_levels.py` — Role-Adjusted Rating
- `investment/grader.py` — A+/A/B/C/D investment classification
- `temporal/age_curves.py` + `decay_weights.py` — Time-based adjustments
- `guardrails/temporal_wall.py` — Train/test temporal split (prevents data leakage)
- `guardrails/overfitting_guard.py` — Adversarial validation checks
- `guardrails/confidence_sampler.py` — Confidence-weighted sampling

### Extraction Pipeline (`extraction/`)

- `scrapers/vlr_resilient_client.py` — VLR.gg scraper with circuit breaker
- `scrapers/epoch_harvester.py` — Epoch I/II/III data extraction
- `parsers/match_parser.py` — Match data parsing
- `parsers/role_classifier.py` — Agent role classification
- `parsers/economy_inference.py` — Economy inference from ACS differentials
- `bridge/extraction_bridge.py` — Converts `EventLog.gd` replay data to `spatial_events` schema
- `storage/integrity_checker.py` — SHA-256 checksum verification
- `storage/raw_repository.py` — Immutable raw data storage
- `storage/reconstruction_repo.py` — Calculated/reconstructed data storage

### Database Migrations (`infrastructure/migrations/`)

Migrations follow a numbered sequence:
1. `001_initial_schema.sql` — 37-field KCRITR player performance schema
2. `002_sator_layers.sql` — spatial_events, sator_events tables
3. `003_dual_storage.sql` — Raw + reconstruction storage tables
4. `004_extraction_log.sql` — Audit and lineage tracking

### SATOR Square Visualization (`visualization/`)

5-layer palindromic visualization (each layer is a React/D3/WebGL component):
- `SatorLayer.tsx` — Hotstreak momentum, pulse animations
- `ArepoLayer.tsx` — Death stains, clutch crowns
- `TenetLayer.tsx` — Area control grading, zone colors
- `OperaLayer.tsx` — Fog of war (WebGL `fog.frag` shader)
- `RotasLayer.tsx` — Rotation trails (WebGL `dust.vert` shader)
- `hooks/useSpatialData.ts` — Data fetching + caching hook

### Adding a new analytics metric

1. Create a new module under `axiom-esports-data/analytics/`
2. Follow the pattern of existing calculators (e.g., `simrating/calculator.py`)
3. Implement `guardrails/temporal_wall.py` constraints — never use future data
4. Add unit tests in the module's `tests/` directory
5. Document the metric in `axiom-esports-data/docs/DATA_DICTIONARY.md`

### Adding a new SATOR visualization layer

1. Create a React component in `axiom-esports-data/visualization/sator-square/`
2. Use D3.js for SVG elements (<200 elements for 60 FPS)
3. Use WebGL for high-element-count renders (>1000 elements)
4. Follow protanopia-safe color palette guidelines
5. Add shader files to `visualization/shaders/` if needed
6. Test with `useSpatialData.ts` hook for data binding

### Running the analytics pipeline

```bash
cd axiom-esports-data
# Start database
docker-compose -f infrastructure/docker-compose.yml up -d
# Run extraction
cd extraction && pip install -r requirements.txt
python src/scrapers/epoch_harvester.py --mode=delta
# Run analytics
cd ../analytics
python -m pytest tests/
```

## Coding Conventions by Stack

### GDScript (Game — `scripts/`)

See the Coding Conventions section above. Key rules:
- Determinism is **critical** — seeded RNG only, fixed timestep, consistent ordering
- Tabs for indentation
- `snake_case` functions/variables, `PascalCase` classes

### Python (Analytics — `axiom-esports-data/`)

- Follow PEP 8 style
- Use type hints for function signatures
- Overfitting guardrails are **critical** — temporal wall must prevent future data leakage
- Use `confidence_sampler.py` for any statistical calculations
- All data must pass through `integrity_checker.py` before analytics

### TypeScript/React (Visualization — `axiom-esports-data/visualization/`)

- Strict TypeScript (`strict: true`)
- React functional components with hooks
- Accessibility: protanopia-safe colors, ARIA labels, keyboard navigation
- Performance: SVG <200 elements, WebGL for dense renders
- Use `useSpatialData.ts` for data fetching

### TypeScript (Packages — `packages/`)

- Strict TypeScript
- Firewall enforcement: all web-facing data must pass through `FantasyDataFilter.sanitizeForWeb()`
- Public types defined in `packages/stats-schema/src/types/`
