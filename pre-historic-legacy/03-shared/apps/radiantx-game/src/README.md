# LiveSeasonModule

GDScript module for extracting match statistics from the Godot tactical FPS simulation and exporting them to the SATOR web platform.

## Overview

The `LiveSeasonModule` is the **primary enforcement point** for the SATOR data partition firewall. It ensures that game-internal data (AI states, RNG seeds, simulation ticks, etc.) never reaches the public web platform.

```
┌──────────────────────────────────────────────────────────────┐
│                     GAME SIMULATION                          │
│  MatchEngine · Agent · EventLog                              │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          ▼
          ┌───────────────────────────┐
          │    LiveSeasonModule       │  ◄── YOU ARE HERE
          │  (sanitization + export)  │
          └───────────────┬───────────┘
                          │  Only PUBLIC fields pass
                          ▼
          ┌───────────────────────────┐
          │      ExportClient         │
          │  (HTTP + retry logic)     │
          └───────────────┬───────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                     SATOR WEB API                            │
└──────────────────────────────────────────────────────────────┘
```

## Files

| File | Purpose |
|------|---------|
| `LiveSeasonModule.gd` | Main module for match data extraction and sanitization |
| `ExportClient.gd` | HTTP client with retry logic and offline queueing |
| `../tests/test_live_season.gd` | Unit tests for sanitization and firewall compliance |

## Quick Start

### 1. Add to Your Scene

```gdscript
# In Main.gd or MatchEngine setup
var live_season_module: LiveSeasonModule

func _ready():
    live_season_module = LiveSeasonModule.new()
    live_season_module.name = "LiveSeasonModule"
    live_season_module.configure(
        "https://api.sator.example.com/matches",
        "your_api_key_here",
        true  # auto_export
    )
    add_child(live_season_module)
    
    # Connect to match end signal
    match_engine.match_ended.connect(_on_match_ended)

func _on_match_ended():
    var match_result = {
        "map": current_map.name,
        "team_a_score": team_a_score,
        "team_b_score": team_b_score,
        "winner": winner,
        "agents": all_agents
    }
    live_season_module.record_match_end(match_result)
```

### 2. Configure via Editor

Select the `LiveSeasonModule` node in the scene and set these exported variables:

- **`api_endpoint`** (String): URL for the SATOR match API
- **`api_key`** (String): Bearer token for authentication
- **`auto_export`** (bool): If true, automatically export when match ends
- **`debug_mode`** (bool): Enable verbose logging

### 3. Manual Export

```gdscript
# Record match without auto-export
live_season_module.record_match_end(match_result)

# Export manually later
var success = live_season_module.export_current_match()

# Get match summary for local storage
var summary = live_season_module.generate_match_summary()
```

## Data Firewall

### GAME-ONLY Fields (NEVER Exported)

These fields are automatically stripped from all exported data:

| Field | Reason |
|-------|--------|
| `internalAgentState` | AI decision tree - could enable counter-play scripting |
| `radarData` | Real-time positions - wall-hack risk |
| `detailedReplayFrameData` | Per-tick frames - full replay extraction risk |
| `simulationTick` | Engine counter - reveals match pacing |
| `seedValue` | RNG seed - allows outcome prediction |
| `visionConeData` | AI vision state - reveals what AI can see |
| `smokeTickData` | Smoke simulation state |
| `recoilPattern` | Weapon data - aimbot scripting risk |

### SAFE Fields (Always Exported)

**Player Stats:**
- Identity: `playerId`, `username`, `team`, `agentId`, `role`
- Combat: `kills`, `deaths`, `assists`, `damage`, `headshots`, `headshotPercentage`
- Performance: `firstKills`, `firstDeaths`, `clutchesWon`, `clutchesLost`, `kast`, `adr`, `kpr`
- Participation: `roundsPlayed`, `roundsWon`, `roundsLost`, `survivalRate`

**Match Metadata:**
- `matchId`, `mapName`, `startedAt`, `endedAt`, `duration`
- `winnerSide`, `roundsPlayed`, `teamAScore`, `teamBScore`

## API Reference

### LiveSeasonModule

#### Signals

```gdscript
signal match_exported(success: bool, match_id: String)
signal sanitization_failed(field_name: String)
```

#### Methods

```gdscript
# Called when match ends - records and optionally exports
func record_match_end(match_result: Dictionary) -> void

# Manually trigger export of recorded match
func export_current_match() -> bool

# Get sanitized match data for local storage
func generate_match_summary() -> Dictionary

# Configure API settings at runtime
func configure(endpoint: String, key: String, auto: bool = false) -> void

# Connect to EventLog for event stream processing
func connect_to_event_log(event_log: Node) -> void

# Get current export status
func get_export_status() -> Dictionary

# Save match data to local file (JSON)
func save_to_file(file_path: String) -> bool
```

### ExportClient

#### Signals

```gdscript
signal request_completed(success: bool, response: Dictionary)
signal queue_flushed()
```

#### Methods

```gdscript
# Send match data to API with automatic retry
func send_match_data(payload: Dictionary) -> bool

# Get current offline queue size
func get_queue_size() -> int

# Check if in offline mode
func is_offline() -> bool

# Clear the offline queue
func clear_queue() -> void

# Get queue contents (for persistence)
func get_queue_contents() -> Array[Dictionary]

# Restore queue from saved data
func restore_queue(saved_queue: Array) -> void
```

## Match Result Format

The module accepts a flexible `match_result` dictionary:

```gdscript
var match_result = {
    # Required match info
    "map": "training_ground",           # or "mapName"
    "team_a_score": 13,
    "team_b_score": 10,
    "winner": "team_a",                 # or 0/1 for team index
    
    # Optional timing
    "duration_ticks": 5000,             # Will convert to seconds (20 TPS)
    "startedAt": "2024-01-15T10:30:00Z",
    
    # Player data (can be Agent nodes or dictionaries)
    "agents": [
        {
            "id": 0,
            "name": "Player1",
            "team": 0,                      # 0 = team_a, 1 = team_b
            "kills": 20,
            "deaths": 10,
            "assists": 5,
            "damage": 2500,
            "headshots": 5,
            # ... other stats
            "internalAgentState": {...}     # Will be stripped!
        },
        # ... more players
    ],
    
    # Round summaries (NOT detailed replay data)
    "rounds": [
        {
            "round_number": 1,
            "winner": "team_a",
            "win_method": "elimination"
        }
    ]
}
```

## Retry Logic & Offline Mode

The `ExportClient` handles network failures gracefully:

1. **Exponential Backoff**: Retries with delays of 1s, 2s, 4s, 8s... up to 60s
2. **Max Retries**: 3 attempts before giving up
3. **Offline Queue**: Failed requests are queued and retried when connection restored
4. **Jitter**: Random 0-1s added to prevent thundering herd

```gdscript
# Check queue status
var status = live_season_module.get_export_status()
print(status.offlineQueueSize)  # Number of pending exports
print(status.isOffline)         # Currently offline?

# The queue is automatically processed when:
# - A successful export completes
# - API endpoint is configured
```

## Testing

Run the test suite:

```bash
# In Godot editor, run the test scene
godot --path simulation-game --scene shared/apps/radiantx-game/tests/test_live_season.tscn
```

Or create a test scene:

```gdscript
# test_live_season.tscn
[gd_scene load_steps=2 format=3 uid="uid://..."]
[ext_resource type="Script" path="res://shared/apps/radiantx-game/tests/test_live_season.gd" id="1_abc123"]
[node name="TestLiveSeason" type="Node"]
script = ExtResource("1_abc123")
```

### Test Coverage

- ✓ Sanitization removes all GAME_ONLY_FIELDS
- ✓ Safe fields are preserved
- ✓ Nested dictionaries and arrays are sanitized
- ✓ Firewall validation detects violations
- ✓ Player stats extraction from nodes and dictionaries
- ✓ Derived stats calculation (ADR, KPR, HS%)
- ✓ Match data structure building
- ✓ Export client queue and retry logic
- ✓ Full export flow integration
- ✓ Offline mode queueing

## Integration with MatchEngine

To integrate with the existing `MatchEngine.gd`:

```gdscript
# In MatchEngine.gd, add signal connection
signal match_ended_with_data(match_result: Dictionary)

func stop_match():
    is_running = false
    
    # Build match result for export
    var match_result = {
        "map": map_data.name if map_data else "unknown",
        "duration_ticks": current_tick,
        "team_a_score": _team_a_rounds_won,
        "team_b_score": _team_b_rounds_won,
        "winner": _last_winner,
        "agents": agents
    }
    
    event_log.log_event({
        "type": "match_end",
        "tick": current_tick,
        "final_score": {
            "team_a": _team_a_rounds_won,
            "team_b": _team_b_rounds_won
        }
    })
    
    match_ended.emit()
    match_ended_with_data.emit(match_result)  # New signal with data
```

Then in `Main.gd`:

```gdscript
func _ready():
    # ... existing setup ...
    match_engine.match_ended_with_data.connect(_on_match_ended_with_data)

func _on_match_ended_with_data(match_result: Dictionary):
    live_season_module.record_match_end(match_result)
```

## Security Considerations

1. **Never log API keys**: The `api_key` is used in headers but not logged
2. **Local file exports are sanitized**: `save_to_file()` runs data through firewall
3. **Queue persistence**: Consider encrypting queued data if it contains sensitive info
4. **HTTPS only**: Always use HTTPS endpoints in production

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Exports failing | Check `get_export_status()` for queue size and offline status |
| Missing player stats | Ensure agent data includes `id` or `agent_id` field |
| Map name not appearing | Use `map` or `mapName` key in match_result |
| Game-only fields leaking | Enable `debug_mode` to see sanitization logs |
| Queue growing | Check network connection and API endpoint configuration |

## Version History

- **1.0.0** (Current): Initial implementation with firewall compliance, retry logic, and offline queueing
