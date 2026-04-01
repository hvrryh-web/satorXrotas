# RadiantX Tactical Sim - Comprehensive Design Review & Gap Analysis Report

**Date:** 2024  
**Purpose:** Professional system design review for evolving RadiantX into a complete Windows-only tactical coaching/manager application  
**Review Scope:** Full repository analysis including Godot simulation app and C# SimCore package

---

## Executive Summary

RadiantX is a well-architected deterministic tactical FPS simulation built with Godot 4 and GDScript, featuring a separate C# combat simulation core. The current implementation provides a solid foundation with deterministic 20 TPS simulation, partial observability, belief systems, and replay functionality. However, to evolve into a complete coaching/manager application, several critical gaps must be addressed in simulation fidelity, coaching-oriented features, UX workflows, data configuration, and testing infrastructure.

**Key Findings:**
- ✅ Strong deterministic simulation core with clear separation of concerns
- ⚠️ Replay system lacks world state reconstruction capability
- ⚠️ No scenario/configuration abstraction for match setup
- ⚠️ Missing coaching-oriented analysis and statistics layer
- ⚠️ Limited agent behavior configurability
- ⚠️ No structured workflow for coach users (menus, replay browser, scenario picker)
- ⚠️ C# SimCore exists but is not integrated with Godot app

**Recommended Path Forward:** Implement a phased roadmap (4 phases) to introduce scenario definitions, replay engine with state reconstruction, analysis layer, agent behavior configs, and coaching UX, while maintaining the existing Godot-based architecture as the primary product.

---

## 1. Current System Architecture Analysis

### 1.1 Godot Simulation Application (`scripts/*.gd`)

#### Core Components

**MatchEngine (`scripts/MatchEngine.gd`)**
- **Purpose:** Central deterministic 20 TPS tick-based simulation engine
- **Key Features:**
  - Fixed timestep (50ms per tick, 20 TPS)
  - Seeded RNG for reproducibility
  - Manages agent array, map data, and event logging
  - Processes agent beliefs, decisions, actions, tactical events, and combat each tick
  - Emits signals for visualization and replay
- **Strengths:**
  - Clean tick loop with deterministic guarantees
  - Well-structured event logging
  - Clear separation between simulation and visualization
- **Limitations:**
  - No explicit match termination/win condition logic (implicit via alive count)
  - No scenario/match configuration abstraction
  - `get_state_at_tick()` exists but replay mode doesn't use it for state reconstruction

**Agent (`scripts/Agent.gd`)**
- **Purpose:** Individual tactical agent with partial observability
- **Key Features:**
  - Belief system tracking other agents (position, health, state, confidence)
  - Belief decay over time when not observed (5% per tick)
  - Vision system with range (50 units), smoke occlusion, flash effects
  - Simple decision-making: move toward known enemies, random exploration
  - Tactical utilities: smoke grenades (5% chance), flashbangs (3% chance)
  - Movement and combat actions
- **Strengths:**
  - Well-implemented partial observability model
  - Clear belief update logic
  - Deterministic behavior
- **Limitations:**
  - Hard-coded behavior parameters (vision range, move speed, utility probabilities)
  - No behavior configuration system
  - Simple decision logic (no advanced tactics)
  - Team identification is implicit (no named rosters/players)

**MapData (`scripts/MapData.gd`)**
- **Purpose:** Map geometry and line-of-sight calculations
- **Key Features:**
  - JSON-based map loading
  - Zone system (spawn points, objectives)
  - Occluder system (walls blocking LOS/bullets)
  - Line-of-sight raycast checks
  - Spawn position resolution by team
- **Strengths:**
  - Clean JSON format
  - Efficient LOS calculations
  - Flexible zone/occluder system
- **Limitations:**
  - No scenario definitions (initial positions, pre-placed utilities, economy state)
  - Map format doesn't support dynamic elements

**EventLog (`scripts/EventLog.gd`)**
- **Purpose:** Event recording for replay functionality
- **Key Features:**
  - Structured event storage (match_start, hit, kill, smoke_deployed, flash_deployed, match_end)
  - Save/load to JSON files
  - Query by tick or range
  - 100k event limit
- **Strengths:**
  - Well-structured event format
  - Efficient storage
  - Good query API
- **Limitations:**
  - No periodic state snapshots (only events)
  - No metadata in replay files (map name, scenario, tags)
  - Events don't include full agent state (only deltas)

**Viewer2D (`scripts/Viewer2D.gd`)**
- **Purpose:** Top-down 2D visualization with interpolation
- **Key Features:**
  - 60 FPS rendering from 20 TPS simulation
  - Interpolated agent positions
  - Color-coded teams (blue/red)
  - Health bars, status indicators, smoke visualization
  - Camera controls
- **Strengths:**
  - Smooth visual experience
  - Clear visual feedback
- **Limitations:**
  - No heatmap or analysis overlays
  - No minimap or tactical view options
  - Limited visual customization

**PlaybackController (`scripts/PlaybackController.gd`)**
- **Purpose:** Playback state and controls
- **Key Features:**
  - Play/pause functionality
  - Variable speed (0.25x to 4x)
  - Timeline scrubbing
  - LIVE vs REPLAY modes
- **Strengths:**
  - Good control API
  - Flexible speed control
- **Limitations:**
  - **Critical Gap:** REPLAY mode only increments `replay_tick` counter; does not reconstruct world state from events
  - No state reconstruction engine
  - Replay mode doesn't drive MatchEngine or Viewer2D with actual replay data

**Main (`scripts/Main.gd`)**
- **Purpose:** Main game controller and HUD
- **Key Features:**
  - Wires all components together
  - Creates and spawns teams (hardcoded 5v5)
  - Basic HUD (time, speed, score labels, buttons, timeline slider)
  - Keyboard controls (Space, arrows, +/-)
  - Replay save/load buttons (load is stubbed)
- **Strengths:**
  - Functional basic UI
  - Good keyboard shortcuts
- **Limitations:**
  - Hardcodes single map (`training_ground.json`)
  - Hardcodes symmetric 5v5 teams
  - No main menu or workflow
  - No replay browser or file picker
  - No scenario selection
  - No configuration UI

### 1.2 C# Combat Simulation Package (`tactical-fps-sim-core-updated/`)

#### Overview
A sophisticated, production-ready combat simulation core written in C# (.NET 8), designed as a standalone package that can be integrated into various applications.

#### Key Components

**SimCore (`SimCore/`)**
- **DefDatabase:** JSON-based definition system for rulesets, agents, weapons, utilities, maps
- **Simulator:** Main simulation engine with tick-based updates
- **Combat Systems:**
  - `RaycastDuelEngine`: Geometry-accurate hitscan combat
  - `TtkDuelEngine`: Fast TTK Monte Carlo for background fights
  - `TwoWayDuel`: Simultaneous engagement resolution
- **Economy System:** Round-based economy with credits, loss streaks, buy system
- **Round System:** Round start/end logic, HP/armor resets, utility refills
- **Utility System:** CS-like grenades and VAL-like abilities
- **Geometry:** Map runtime, raycast 2D, smoke fields

**Console Runners**
- `ConsoleRunner`: Basic console app for testing
- `SimConsoleRunner`: Full simulation runner with economy and rounds

**TypeScript Schemas (`SchemasTS/types.ts`)**
- Mirrored TypeScript types for UI tools/viewers

#### Strengths
- **Production-ready combat logic** with sophisticated duel engines
- **Rich configuration system** via JSON Defs
- **Economy and round systems** for tactical FPS gameplay
- **Well-structured** with clear separation of concerns
- **Extensible** architecture

#### Current Status
- **Not integrated** with Godot app
- **Separate data models** (Godot uses simple maps, C# uses rich Defs)
- **No shared schema** between Godot and C# systems
- **Potential future backend** for advanced simulation modes

### 1.3 Documentation & Developer Tooling

#### Documentation (`docs/`)
- ✅ Comprehensive architecture overview
- ✅ Map format specification
- ✅ Agent behavior documentation
- ✅ Replay system guide
- ✅ Quick start guide
- ✅ Custom agents documentation (006/007/47 for AI-assisted development)

#### Testing
- ✅ Determinism test scene (`tests/test_determinism.gd`)
- ✅ Tests verify same seed = same results
- ⚠️ No automated CI tests visible
- ⚠️ No tests for coaching workflows (scenario loading, replay navigation, stats)

#### Project Structure
- Clean separation of concerns
- Well-organized file structure
- Good naming conventions

---

## 2. Key Strengths

1. **Deterministic Core**
   - Clear 20 TPS tick loop with seeded RNG
   - Reproducible matches enable testing and analysis
   - Well-documented determinism guarantees

2. **Simple, Inspectable AI**
   - Belief system is readable and easy to modify
   - Clear partial observability model
   - Good foundation for extending agent behaviors

3. **Replay Model**
   - Structured event format supports deeper analysis
   - Save/load functionality exists
   - Events capture key match moments

4. **Clean Architecture**
   - Good separation: simulation (MatchEngine/Agent/MapData), visualization (Viewer2D), control (PlaybackController/Main)
   - Modular design allows extension

5. **Rich External Combat Core**
   - C# SimCore provides advanced combat simulation
   - Can serve as future backend upgrade path
   - Production-ready duel engines and economy systems

---

## 3. Design & Implementation Gaps (Coach App Lens)

### 3.1 Simulation & Replay Fidelity

#### Gap: Replay State Reconstruction
**Issue:** Replay playback currently only increments `replay_tick` in `PlaybackController._process_replay()`. It does not reconstruct world state from `EventLog` events. The same agents from the last live match are reused, not driven by replay data.

**Impact:** Coaches cannot properly review matches; replay mode is essentially non-functional for analysis.

**Evidence:**
- `PlaybackController.load_replay()` stores events but doesn't reconstruct state
- `_process_replay()` only increments `replay_tick` and emits signals
- No `ReplayEngine` that can produce agent states from events
- `MatchEngine.get_state_at_tick()` exists but is unused in replay mode

**Recommendation:**
- Implement a `ReplayEngine` that can reconstruct world state from events
- Either log periodic snapshots or ensure events contain enough state to replay deterministically
- Update `PlaybackController` REPLAY mode to use `ReplayEngine` to drive `MatchEngine` and `Viewer2D`

#### Gap: Match Termination Logic
**Issue:** Match termination is implicit (HUD counts alive agents) rather than canonical logic in `MatchEngine`. No explicit win condition checking.

**Impact:** Matches may run indefinitely or terminate inconsistently.

**Recommendation:**
- Add explicit win condition checking in `MatchEngine.process_tick()`
- Define win conditions (e.g., eliminate all enemies, objective capture, time limit)
- Emit `match_ended` signal with winner information

#### Gap: No Match/Scenario Configuration Abstraction
**Issue:** `Main._start_new_match()` hardcodes:
- Single map (`training_ground.json`)
- Symmetric 5v5 teams
- No scenario definitions (initial positions, economy, pre-placed utilities)

**Impact:** Cannot run different scenarios, test specific situations, or configure matches for coaching purposes.

**Recommendation:**
- Introduce `ScenarioDef` JSON format describing: map, team comps, starting positions, initial utilities, seed, win conditions
- Add `ScenarioLoader` module that converts `ScenarioDef` → `MapData` + configured `Agent` arrays
- Create `MatchSession` orchestrator that takes `ScenarioDef` and runs full lifecycle

### 3.2 Coaching/Manager Features

#### Gap: No Team/Roster/Player Identity System
**Issue:** Agents only have numeric `agent_id` and team enum. No concept of:
- Named players/rosters
- Player profiles or statistics
- Team compositions beyond "5v5"

**Impact:** Cannot track individual player performance, create custom teams, or build coaching profiles.

**Recommendation:**
- Introduce `PlayerDef` and `RosterDef` JSON schemas
- Add player names, roles, and metadata to agents
- Track per-player statistics across matches

#### Gap: No Scenario Presets
**Issue:** No predefined scenarios for tactical training:
- Eco rounds
- Post-plant situations
- Retake scenarios
- Specific map positions

**Impact:** Cannot run targeted tactical training exercises.

**Recommendation:**
- Create `scenarios/` directory with scenario JSON files
- Build scenario library (eco, post-plant, retake, etc.)
- Add scenario picker UI

#### Gap: No Analysis Layer
**Issue:** Events are logged but not analyzed. No statistics, heatmaps, utility tracking, or match dashboards.

**Impact:** Coaches cannot extract insights from matches; manual analysis required.

**Recommendation:**
- Implement `AnalysisEngine` or `MatchStats` module
- Process `EventLog` into statistics (kills, deaths, damage, utility usage, time-to-contact)
- Generate heatmaps, timelines, and summary reports
- Surface stats in UI (dashboard, side panel, tabs)

#### Gap: No Persistent Profile/Season Model
**Issue:** No concept of:
- Coach profiles or sessions
- Saved configurations
- Scenario libraries
- Match history

**Impact:** Cannot build a coaching workflow or track progress over time.

**Recommendation:**
- Add user profile system (JSON-based for simplicity)
- Save match configurations and scenarios
- Build match history with metadata

### 3.3 UX & Workflow

#### Gap: No Main Menu or Workflow
**Issue:** Application drops directly into a match. No:
- Main menu
- Scenario selection
- Replay browser
- Settings/configuration

**Impact:** Poor user experience; coaches cannot navigate the application effectively.

**Recommendation:**
- Create `MainMenu` scene with options: "Quick Match", "Scenarios", "Replays", "Settings"
- Implement workflow: Home → Configure → Run Match → Review → Save/Tag Replay

#### Gap: Replay Load is Stubbed
**Issue:** `Main._on_load_replay_pressed()` prints "Load replay not fully implemented yet". No:
- File picker
- Replay browser
- Metadata display (map, date, duration, scores)

**Impact:** Cannot load and review saved replays.

**Recommendation:**
- Implement replay browser panel listing replay files from `user://`
- Show metadata (map name, seed, date, duration, team scores)
- Add file picker or list selection
- Load replay and switch to replay mode

#### Gap: Minimal HUD for Coaching
**Issue:** Current HUD shows basic info (time, speed, score) but lacks:
- Stats overlay
- Timeline with event markers
- Agent information panel
- Utility usage tracking

**Impact:** Limited visibility into match state for coaching analysis.

**Recommendation:**
- Enhance HUD with stats panel (kills, deaths, damage, utilities)
- Add timeline with event markers (kills, smokes, flashes)
- Create agent info panel showing selected agent's beliefs and state
- Add utility usage visualization

### 3.4 Data & Configuration Design

#### Gap: No Scenario Definition Schema
**Issue:** Maps are JSON-only. No shared schema for:
- Scenario definitions (initial positions, roles, economy, pre-placed smokes)
- Agent behavior configurations
- Match rules/variants

**Impact:** Cannot define reusable scenarios or configure matches programmatically.

**Recommendation:**
- Define `ScenarioDef` JSON schema
- Include: map reference, team comps, starting positions, initial utilities, seed, win conditions
- Create `ScenarioLoader` to parse and instantiate scenarios

#### Gap: Agent Behavior is Hard-Coded
**Issue:** Agent behavior parameters are hard-coded in `Agent.gd`:
- Vision range: 50 units
- Move speed: 5.0 units/tick
- Utility probabilities: 5% smoke, 3% flash
- Decision logic: simple random selection

**Impact:** Cannot customize agent behaviors for coaching scenarios or testing different tactics.

**Recommendation:**
- Define `AgentBehaviorDef` JSON schema (aggression, utility rates, preferred zones, pathing style)
- Modify `Agent` to read behavior from config struct
- Create behavior presets (Aggressive, Default, Passive, Lurker)
- Expose in coach UI for per-agent or per-team configuration

#### Gap: Godot and C# Data Models Are Separate
**Issue:** Godot uses simple map format; C# uses rich `Defs` system. No alignment or shared schema.

**Impact:** Cannot leverage C# SimCore features; two separate worlds.

**Recommendation (Future Phase):**
- Define shared JSON format for weapons/utilities/rules
- Create bridge/adapter layer if integrating C# SimCore
- Consider CLI/pipe-based integration first before native module

### 3.5 Testing & QA for Coach App

#### Gap: No Coaching Workflow Tests
**Issue:** Determinism tests exist but no tests for:
- Scenario loading
- Replay navigation
- Stats correctness
- UI flows

**Impact:** Cannot ensure coaching features work correctly; regression risk.

**Recommendation:**
- Add automated tests for scenario loading
- Test replay round-trips (record → reload → compare)
- Validate stats calculations
- Create fixture library of maps/scenarios and golden event logs

#### Gap: No Acceptance Criteria for Coach App
**Issue:** No formal acceptance criteria or test plan for coaching application features.

**Impact:** Unclear what "complete" means for a coach app.

**Recommendation:**
- Define acceptance criteria for each phase
- Create test plan covering: scenario selection, match execution, replay review, stats analysis
- Establish QA process for coach workflows

---

## 4. Recommended Target Architecture

### 4.1 High-Level Architecture

Use the existing Godot project as the **primary product shell**, treating C# SimCore as an optional future backend upgrade. Introduce clearer layers:

```
┌─────────────────────────────────────────────────────────┐
│                  CoachUI_Godot                          │
│  (MainMenu, MatchSession, ReplayView, AnalysisPanel)   │
└──────────────┬──────────────────────┬────────────────────┘
               │                      │
    ┌──────────▼──────────┐  ┌───────▼────────┐
    │ MatchOrchestrator   │  │ ReplayBrowser  │
    │                     │  │                │
    │ - ScenarioLoader    │  │ - File listing │
    │ - MatchSession      │  │ - Metadata     │
    └──────────┬──────────┘  └────────────────┘
               │
    ┌──────────▼──────────┐
    │   MatchEngine       │
    │   (GDScript)        │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │   EventLog          │
    └──────────┬───────────┘
               │
    ┌──────────┴───────────┐
    │                      │
┌───▼──────────┐  ┌────────▼────────┐
│ ReplayEngine │  │ AnalysisEngine  │
│              │  │                 │
│ - State      │  │ - Stats         │
│   recon      │  │ - Heatmaps      │
│ - Scrub      │  │ - Reports       │
└──────────────┘  └─────────────────┘

┌─────────────────────────────────────┐
│      JSON Data Layer                │
│  - MapDefs                          │
│  - ScenarioDefs                     │
│  - AgentBehaviorDefs                │
│  - ReplayMetadata                   │
└─────────────────────────────────────┘
```

### 4.2 Component Descriptions

**CoachUI_Godot**
- Top-level scenes and HUD for configuring matches, running them, inspecting replays/stats
- MainMenu, MatchSession, ReplayView, AnalysisPanel scenes

**MatchOrchestrator**
- Small layer (part of `Main` or dedicated `MatchSession` node)
- Takes `ScenarioDef` and spins up `MatchEngine`, agents, maps
- Manages match lifecycle: load → spawn → run → save replay

**ScenarioLoader/Data Layer**
- JSON definitions for maps, scenarios, agent behaviors, rule sets
- Godot-side loader producing `MapData` and agent instances
- Validates and instantiates scenarios

**ReplayEngine**
- Reconstructs world state from `EventLog` events at any tick
- Decoupled from live simulation
- Supports scrubbing and fast-forwarding
- Produces agent states for visualization

**AnalysisEngine**
- Processes events into statistics and derived views
- Generates: kills/deaths/assists, damage over time, utility usage, heatmaps, timelines
- Used by UI for dashboards and reports

### 4.3 Data Model

#### ScenarioDef JSON Schema
```json
{
  "id": "eco_round_retake",
  "name": "Eco Round Retake",
  "description": "Defenders have planted, attackers retake with pistols",
  "map": "training_ground",
  "seed": 12345,
  "win_conditions": {
    "type": "elimination",
    "time_limit_ticks": 1200
  },
  "teams": {
    "team_a": {
      "name": "Attackers",
      "agents": [
        {
          "player_id": "player_1",
          "behavior": "aggressive",
          "spawn_zone": "spawn_a",
          "initial_utilities": ["flash"]
        }
      ]
    },
    "team_b": {
      "name": "Defenders",
      "agents": [
        {
          "player_id": "player_6",
          "behavior": "defensive",
          "spawn_zone": "objective_a",
          "initial_utilities": ["smoke"]
        }
      ]
    }
  },
  "pre_placed_utilities": [
    {
      "type": "smoke",
      "position": {"x": 45, "y": 45},
      "deploy_tick": 0
    }
  ]
}
```

#### AgentBehaviorDef JSON Schema
```json
{
  "id": "aggressive",
  "name": "Aggressive",
  "vision_range": 60.0,
  "move_speed": 6.0,
  "aggression_level": 0.8,
  "utility_usage": {
    "smoke_probability": 0.08,
    "flash_probability": 0.05
  },
  "decision_weights": {
    "push_enemy": 0.7,
    "hold_position": 0.2,
    "flank": 0.1
  }
}
```

#### ReplayMetadata JSON Schema
```json
{
  "replay_id": "replay_2024-12-16_10-30-00",
  "map": "training_ground",
  "scenario": "standard_5v5",
  "seed": 12345,
  "date": "2024-12-16T10:30:00Z",
  "duration_ticks": 1500,
  "team_a_score": 5,
  "team_b_score": 3,
  "tags": ["practice", "retake"]
}
```

---

## 5. Concrete Design Gaps & Suggested Improvements

### Gap A: Weak Match/Scenario Abstraction

**Current State:**
- `Main._start_new_match()` hardcodes single 5v5 spawn and map
- No scenario or team configuration concept

**Recommended Solution:**
1. Introduce `ScenarioDef` JSON format in `scenarios/` directory
2. Add `ScenarioLoader` module (GDScript) converting `ScenarioDef` → `MapData` + configured `Agent` arrays
3. Evolve `Main` or create `MatchSession` script taking `ScenarioDef` name and running full lifecycle

**Implementation Steps:**
- Create `scripts/ScenarioLoader.gd` with `load_scenario(scenario_id: String) -> ScenarioDef`
- Define `ScenarioDef` class/resource
- Create 2-3 example scenarios (standard_5v5, eco_retake, post_plant)
- Update `Main` to use `ScenarioLoader`

### Gap B: Replay as Ticks-Only, Not State

**Current State:**
- Replay mode uses `replay_tick` and events but no world reconstruction
- Same agents from last run are reused

**Recommended Solution:**
1. Define state-from-events model: log periodic snapshots or ensure events contain full state
2. Implement `ReplayEngine` that:
   - Produces agent states for any tick (fast-forward or snapshot + delta)
   - Drives `Viewer2D` and HUD from replay state
3. Update `PlaybackController` REPLAY mode to use `ReplayEngine`

**Implementation Steps:**
- Create `scripts/ReplayEngine.gd`
- Add periodic state snapshots to `EventLog` (every N ticks or on key events)
- Implement `ReplayEngine.reconstruct_state_at_tick(tick: int) -> Dictionary`
- Update `PlaybackController._process_replay()` to call `ReplayEngine` and apply state to `MatchEngine`

### Gap C: No Coaching-Oriented Analysis Layer

**Current State:**
- Events are rich but no built-in analytics

**Recommended Solution:**
1. Introduce `AnalysisEngine` or `MatchStats` module operating on `EventLog`
2. Provide built-in reports: kills/deaths/assists, damage over time, utility casts per area, first contact times
3. Surface stats via HUD panel (tabs: "Overview", "Timeline", "Utilities")

**Implementation Steps:**
- Create `scripts/AnalysisEngine.gd`
- Implement `calculate_stats(event_log: EventLog) -> Dictionary`
- Add stats panel to `Main` HUD
- Display stats in real-time during match/replay

### Gap D: Agent Behavior Configurability

**Current State:**
- Agent behavior hard-coded in `Agent.gd`

**Recommended Solution:**
1. Define `AgentBehaviorDef` JSON schema
2. Modify `Agent` to read behavior from config struct
3. Expose behavior presets in coach UI

**Implementation Steps:**
- Create `AgentBehaviorDef` resource/class
- Add behavior config files in `behaviors/` directory
- Modify `Agent` constructor to accept `AgentBehaviorDef`
- Update `ScenarioLoader` to load and apply behaviors
- Add behavior picker to coach UI

### Gap E: UX & Workflow for Coach

**Current State:**
- No main menu or workflow
- Drops directly into match

**Recommended Solution:**
1. Add main menu scene with: "Quick Match", "Scenarios", "Replays", "Settings"
2. Implement Replays screen listing replay files with metadata
3. Add Scenario picker showing available scenarios

**Implementation Steps:**
- Create `scenes/MainMenu.tscn` and `scripts/MainMenu.gd`
- Create `scenes/ReplayBrowser.tscn` and `scripts/ReplayBrowser.gd`
- Create `scenes/ScenarioPicker.tscn` and `scripts/ScenarioPicker.gd`
- Update project to start with `MainMenu` instead of `Main`
- Implement scene transitions

### Gap F: Integration Strategy with C# SimCore (Optional Future)

**Current State:**
- C# SimCore exists but unused and not aligned with Godot data

**Recommended Solution (Future Phase):**
1. Define shared `Defs`-like JSON format for weapons/utilities/rules
2. Explore CLI/pipe-based integration on Windows first
3. Consider native module integration later

**Implementation Steps (Future):**
- Create shared JSON schema definitions
- Build CLI wrapper around C# SimCore
- Implement event stream protocol
- Create adapter layer in Godot

---

## 6. Phased Roadmap Toward Testable Coach App

### Phase 1: Firm Up Simulation & Replay (Foundation)

**Goal:** Establish solid simulation and replay infrastructure

**Tasks:**
1. Extract `MatchSession` orchestrator from `Main` HUD logic
   - Create `scripts/MatchSession.gd`
   - Move match setup/teardown logic
   - Decouple from UI

2. Implement basic `ScenarioDef` + loader
   - Create `ScenarioDef` class and JSON schema
   - Implement `ScenarioLoader.gd`
   - Support 2-3 canned scenarios (standard_5v5, eco_retake, post_plant)
   - Update `Main` to use scenarios

3. Add `ReplayEngine` with state reconstruction
   - Create `scripts/ReplayEngine.gd`
   - Implement state reconstruction from events (start with forward simulation)
   - Add periodic snapshots to `EventLog` (every 100 ticks)
   - Update `PlaybackController` to use `ReplayEngine`

4. Extend determinism tests
   - Test scenario loading
   - Test replay round-trips (record → reload → compare state)
   - Add golden file tests

**Deliverables:**
- `MatchSession` orchestrator
- `ScenarioLoader` with 2-3 scenarios
- `ReplayEngine` with basic state reconstruction
- Extended test suite

**Acceptance Criteria:**
- Can load different scenarios and run matches
- Can save replay and load it back with correct state
- Replay scrubbing works correctly
- Determinism tests pass

### Phase 2: Coaching UX and Analysis Basics

**Goal:** Build coaching-oriented user experience and basic analysis

**Tasks:**
1. Replace single-scene flow with multi-scene workflow
   - Create `MainMenu` scene
   - Create `MatchSession` scene (extracted from `Main`)
   - Create `ReplayView` scene
   - Implement scene transitions

2. Implement Replay Browser panel
   - List replay files from `user://`
   - Show metadata (map, date, duration, scores)
   - Load replay on selection
   - Add file picker or list UI

3. Implement Scenario Picker panel
   - List available scenario JSONs
   - Show scenario descriptions
   - Load scenario on selection

4. Add `AnalysisEngine` with first dashboard
   - Create `scripts/AnalysisEngine.gd`
   - Calculate: per-agent kills, deaths, damage, utility casts
   - Generate summary statistics

5. Enhance HUD with stats overlay
   - Add stats panel to match/replay view
   - Display real-time statistics
   - Add tabs: "Overview", "Timeline", "Utilities"

**Deliverables:**
- MainMenu, MatchSession, ReplayView scenes
- ReplayBrowser and ScenarioPicker panels
- `AnalysisEngine` with basic stats
- Enhanced HUD with stats display

**Acceptance Criteria:**
- Can navigate: MainMenu → Scenario → Match → Replay
- Can browse and load replays
- Can select scenarios
- Stats display correctly during match/replay

### Phase 3: Agent Configuration & Scenario Richness

**Goal:** Enable agent behavior customization and richer scenarios

**Tasks:**
1. Introduce `AgentBehaviorDef` JSON and migrate `Agent` behavior constants
   - Create `AgentBehaviorDef` class
   - Create behavior config files (aggressive, defensive, passive, lurker)
   - Modify `Agent` to read from config
   - Update `Agent.make_decision()` to use behavior weights

2. Build minimal Team/Agent editor in Godot
   - Create `scenes/TeamEditor.tscn` and `scripts/TeamEditor.gd`
   - Allow coach to pick behaviors per agent
   - Save team configs as named JSON files

3. Extend `ScenarioDef` to reference named agent behaviors
   - Update scenario schema to include behavior references
   - Support economy states or utility loadouts in scenarios
   - Create more complex scenarios (eco, force buy, post-plant)

**Deliverables:**
- `AgentBehaviorDef` system
- Team/Agent editor UI
- Extended scenarios with behavior configs
- Updated `ScenarioLoader` to apply behaviors

**Acceptance Criteria:**
- Can configure agent behaviors per agent or per team
- Can save and load team configurations
- Scenarios can specify agent behaviors
- Different behaviors produce different tactical outcomes

### Phase 4: QA, Tooling, and Optional C# Integration

**Goal:** Ensure quality and explore advanced features

**Tasks:**
1. Add automated tests for coaching workflows
   - Test scenario loading with various scenarios
   - Test replay browsing and loading
   - Test stats correctness (golden files)
   - Test UI flows where possible

2. Introduce CLI wrapper around Godot app (if useful)
   - Batch-generate replays for analysis
   - Export stats to JSON/CSV
   - Run scenarios headlessly

3. Optionally explore C# SimCore integration
   - Define shared JSON schema for weapons/utilities/rules
   - Build CLI wrapper around C# SimCore
   - Implement event stream protocol
   - Create adapter layer in Godot (if desired)

**Deliverables:**
- Comprehensive test suite
- CLI tools (optional)
- C# integration proof-of-concept (optional)

**Acceptance Criteria:**
- All tests pass
- Coaching workflows are tested and stable
- Optional: Can run C# SimCore as backend for specific modes

---

## 7. HT3 Team Application

### Agent 47 (UI/UX Visual Design & Accessibility)

**Focus Areas:**
- Coach-facing flows: menus, scenario/replay browsers, stats panels
- Ensure HUD and interactions are intuitive for tactical analysis
- Accessibility: keyboard navigation, clear visual hierarchy, readable fonts

**Recommendations:**
- Design main menu with clear visual hierarchy
- Create consistent UI patterns across scenes
- Ensure stats panels are readable and well-organized
- Add keyboard shortcuts for all major actions
- Use color coding consistently (teams, status, events)

### Agent 007 (Elite Games Developer & Coding Savant)

**Focus Areas:**
- Simulation loop, replay engine, AI behavior abstractions
- Ensure robustness, determinism, and extensibility
- Game architecture patterns and optimization

**Recommendations:**
- Implement replay engine with efficient state reconstruction
- Design agent behavior system for extensibility
- Optimize simulation performance for larger scenarios
- Ensure determinism is maintained across all new features
- Use proper game architecture patterns (state machines, event systems)

### Agent 006 (Backend Architecture & Infrastructure Savant)

**Focus Areas:**
- JSON data models (`ScenarioDef`, `AgentBehaviorDef`, shared `Defs`)
- Long-term maintainability
- Hooks for future C# SimCore integration or external tooling

**Recommendations:**
- Design JSON schemas with versioning in mind
- Create validation for all JSON configs
- Design data models to support future extensions
- Consider migration paths if integrating C# SimCore
- Plan for potential API/external tooling integration

---

## 8. Implementation Priority & Risk Assessment

### High Priority (Phase 1)
- **ReplayEngine with state reconstruction** - Critical for coach app functionality
- **ScenarioDef + ScenarioLoader** - Foundation for match configuration
- **MatchSession orchestrator** - Clean architecture separation

**Risk:** Medium - Replay state reconstruction is complex but well-defined

### Medium Priority (Phase 2)
- **MainMenu and workflow** - Essential UX but can be iterative
- **ReplayBrowser** - Important but straightforward
- **AnalysisEngine basics** - Core coaching feature

**Risk:** Low - Well-understood requirements

### Lower Priority (Phase 3-4)
- **Agent behavior system** - Enhances functionality but not critical
- **C# integration** - Future enhancement, optional
- **Advanced testing** - Important but can be incremental

**Risk:** Low to Medium - Agent behavior system is straightforward; C# integration is complex but optional

---

## 9. Success Metrics

### Technical Metrics
- ✅ Replay state reconstruction accuracy: 100% match with original simulation
- ✅ Scenario loading success rate: 100%
- ✅ Determinism maintained across all new features
- ✅ Performance: 20 TPS maintained with all features

### User Experience Metrics
- ✅ Can complete full workflow: Menu → Scenario → Match → Replay → Analysis
- ✅ Replay loading time: < 1 second for typical matches
- ✅ Stats calculation: Real-time during match/replay
- ✅ UI responsiveness: 60 FPS maintained

### Coaching Feature Metrics
- ✅ Number of scenarios available: 5+ by end of Phase 3
- ✅ Number of agent behavior presets: 4+ by end of Phase 3
- ✅ Stats available: Kills, deaths, damage, utility usage, timelines
- ✅ Replay browser: Can list and load all saved replays

---

## 10. Conclusion

RadiantX has a strong foundation with a deterministic simulation core, clean architecture, and good documentation. To evolve into a complete coaching/manager application, the primary gaps to address are:

1. **Replay state reconstruction** - Critical for match review
2. **Scenario/configuration system** - Essential for coaching workflows
3. **Analysis layer** - Core coaching feature
4. **Coaching UX** - Required for usability
5. **Agent behavior configurability** - Enhances tactical training

The recommended phased approach (4 phases) allows incremental development while maintaining system stability and determinism. The existing Godot-based architecture should remain the primary product, with C# SimCore integration as an optional future enhancement.

**Next Steps:**
1. Review and approve this design review
2. Prioritize phases based on coaching needs
3. Begin Phase 1 implementation
4. Iterate based on feedback and testing

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**Author:** HT3 Team (Agents 006, 007, 47)  
**Status:** Ready for Implementation

