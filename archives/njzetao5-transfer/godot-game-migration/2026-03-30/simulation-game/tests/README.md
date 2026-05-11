# Godot Test Suite

[Ver001.000]

This directory contains the GUT (Godot Unit Testing) framework and all tests for the RadiantX Tactical FPS Simulation.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_combat_resolver.gd    # Combat resolution logic
│   ├── test_duel_resolver.gd      # Duel mechanics
│   ├── test_economy_simulation.gd # Economy system
│   ├── test_player_movement.gd    # Movement mechanics
│   ├── test_weapon_mechanics.gd   # Weapon systems
│   └── test_round_management.gd   # Round/match state
├── integration/             # Integration tests
├── test_determinism.gd      # Determinism verification
├── test_determinism.tscn    # Determinism test scene
├── run_tests.gd             # Test runner script
└── README.md                # This file
```

## Running Tests

### From Command Line

```bash
# Run all tests
godot --headless --script tests/run_tests.gd

# Run determinism tests specifically
godot --headless tests/test_determinism.tscn
```

### From Godot Editor

1. Install GUT addon (if not already installed)
2. Open the GUT panel: Project > Tools > GUT
3. Click "Run All"

## Test Categories

### Unit Tests

- **Combat Resolver**: Tests hit calculation, damage application, and legacy combat fallback
- **Duel Resolver**: Tests LOD determination, win probability, and batch resolution
- **Economy Simulation**: Tests buy system, money management, and loss bonus
- **Player Movement**: Tests velocity, friction, and movement states
- **Weapon Mechanics**: Tests firing, reloading, accuracy, and damage falloff
- **Round Management**: Tests round state, win conditions, and match flow

### Integration Tests

Integration tests verify component interactions and end-to-end scenarios.

### Determinism Tests

Verifies that simulations are reproducible with the same seed:
- Same seed produces same results
- Different seeds produce different results
- Replay consistency

## Writing New Tests

### Basic Test Structure

```gdscript
extends "res://addons/gut/GutTest.gd"

var component_under_test

func before_each():
    component_under_test = Component.new()

func after_each():
    component_under_test = null

func test_something():
    var result = component_under_test.do_something()
    assert_eq(result, expected_value, "Should return expected value")
```

### Assertions Available

- `assert_eq(a, b, msg)` - Equal
- `assert_ne(a, b, msg)` - Not equal
- `assert_gt(a, b, msg)` - Greater than
- `assert_lt(a, b, msg)` - Less than
- `assert_between(v, a, b, msg)` - Between values
- `assert_true(v, msg)` - True
- `assert_false(v, msg)` - False
- `assert_not_null(v, msg)` - Not null
- `assert_has(obj, key, msg)` - Has property

## CI/CD Integration

Tests are automatically run in GitHub Actions on every push to main/develop branches.

See `.github/workflows/ci.yml` for configuration.
