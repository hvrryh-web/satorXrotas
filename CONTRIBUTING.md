# Contributing to SATOR / RadiantX

Thank you for your interest in contributing to SATOR!

## Project Philosophy

SATOR is a **three-part esports simulation and analytics platform**:
1. **RadiantX** — An offline, deterministic tactical FPS simulation game (Godot 4 / GDScript)
2. **Axiom Esports Data** — A tactical FPS analytics pipeline with SATOR Square visualization (Python + React/TS/D3/WebGL)
3. **SATOR Web** — An online public statistics platform (TypeScript, in development)

All contributions must respect:

1. **Determinism First**: All simulation logic must be deterministic
2. **Firewall Enforced**: Game-internal data must never reach the web platform
3. **Guardrails Enforced**: Analytics must prevent temporal leakage and overfitting
4. **Offline Capable**: Game requires no internet connectivity
5. **Accessible**: Visualization must meet protanopia-safe color standards
6. **Simulation Heavy**: Focus on tactical depth, not graphics

## Firewall Policy

Before contributing any code that involves data flow between the game and web platform,
read **[docs/FIREWALL_POLICY.md](docs/FIREWALL_POLICY.md)**.

The firewall prevents these game-internal fields from ever reaching the web:
`internalAgentState`, `radarData`, `detailedReplayFrameData`, `simulationTick`,
`seedValue`, `visionConeData`, `smokeTickData`, `recoilPattern`

Enforcement is in `packages/data-partition-lib/src/FantasyDataFilter.ts`.
Public type definitions are in `packages/stats-schema/src/types/`.

## Branch Strategy

See **[docs/BRANCH_STRATEGY.md](docs/BRANCH_STRATEGY.md)** for the full branching model.

| Branch | Purpose |
|--------|---------|
| `main` | Production — all tests pass, firewall enforced |
| `develop` | Integration — features merged here before main |
| `feature/*` | Feature development |

- **Always branch from `develop`** for new features
- **Open PRs to `develop`**, not `main`
- PRs to `main` require `@hvrryh-web` approval

## How to Contribute

### Reporting Issues

- Use GitHub Issues
- Include Godot version (for game bugs)
- Describe expected vs actual behavior
- Include steps to reproduce
- Attach replay files if relevant

### Suggesting Features

Features should enhance tactical simulation or the stats platform:
- New tactical utilities (grenades, equipment)
- Improved agent AI
- Analysis tools
- Map editor
- Performance improvements
- Public stats (must comply with firewall policy)

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch from `develop`**
   ```bash
   git checkout -b feature/your-feature-name develop
   ```

3. **Follow coding standards** (see below)

4. **Maintain the firewall** — if your feature produces new data, classify it:
   - Game-internal → add to `FantasyDataFilter.GAME_ONLY_FIELDS`
   - Public stat → add to `packages/stats-schema/src/types/Statistics.ts`

5. **Update documentation**
   - Add docs for new features
   - Update existing docs if behavior changes
   - Update `docs/FIREWALL_POLICY.md` if data classification changes

6. **Test your changes**
   - Run determinism tests (GDScript)
   - Run `npm run test:firewall` (TypeScript)
   - Run `npm run validate:schema` (schema)
   - Verify CI passes

7. **Submit a pull request to `develop`**
   - Describe what changed and why
   - Reference any related issues
   - Include before/after behavior

## Coding Standards

### GDScript Style (Game — `scripts/`)

**Determinism rules apply.** All simulation logic must be deterministic.

```gdscript
# Use snake_case for variables and functions
var agent_health: float = 100.0

func calculate_damage(attacker: Agent, target: Agent) -> float:
	# Use tabs for indentation
	var base_damage = 25.0
	return base_damage

# Use PascalCase for classes
class_name MatchEngine

# Document public functions
func start_match(seed: int):
	"""Start a new match with given seed"""
	pass
```

Key rules:
- Only use seeded RNG — never use `randf()` or `randi()` directly
- Fixed timestep (20 TPS, 50ms) — never use delta-time in simulation logic
- Consistent ordering — process agents/actions in the same order every tick

### Python Style (Analytics — `axiom-esports-data/`)

**Overfitting guardrails apply.** Analytics must prevent temporal leakage.

```python
# Follow PEP 8 style
from typing import Dict, List, Optional

def calculate_simrating(
    player_stats: Dict[str, float],
    role: str,
    confidence: float = 1.0
) -> float:
    """Calculate 5-component SimRating for a player."""
    # Use type hints for all function signatures
    # Temporal wall: never use future data in calculations
    pass
```

Key rules:
- All data must pass through `integrity_checker.py` before analytics
- Use `temporal_wall.py` to enforce train/test temporal splits
- Use `confidence_sampler.py` for confidence-weighted calculations
- SHA-256 checksums for data lineage tracking

### TypeScript/React Style (Visualization — `axiom-esports-data/visualization/`)

**Accessibility standards apply.** All visualizations must be protanopia-safe.

```typescript
// Strict TypeScript mode
import { useSpatialData } from '../hooks/useSpatialData';

// React functional components with hooks
const SatorLayer: React.FC<SatorLayerProps> = ({ matchId, round }) => {
  const { data, loading } = useSpatialData(matchId, round);
  // ARIA labels for accessibility
  // Protanopia-safe color palette
  return <svg aria-label="SATOR hotstreak visualization">...</svg>;
};
```

Key rules:
- SVG for <200 elements (D3.js), WebGL for >1000 elements
- Protanopia-safe color palette (no red-green only distinctions)
- ARIA labels and keyboard navigation support
- Target 60 FPS rendering performance

### TypeScript Style (Packages — `packages/`)

**Firewall enforcement applies.** Game-internal data must never reach the web.

```typescript
// Use strict mode
import type { Statistics } from '@sator/stats-schema';

// Always sanitize game data before sending to API
import { FantasyDataFilter } from '@sator/data-partition-lib';
const safe = FantasyDataFilter.sanitizeForWeb(rawData);
```

### PLpgSQL Style (Migrations — `axiom-esports-data/infrastructure/migrations/`)

**Dual-storage protocol applies.** Raw data is immutable; reconstructed data is calculated.

```sql
-- Numbered migration files: 001_, 002_, etc.
-- Always include rollback (DOWN) migration
-- Use snake_case for table and column names
-- Add comments for complex constraints
CREATE TABLE player_performance (
    id SERIAL PRIMARY KEY,
    player_id VARCHAR(64) NOT NULL,
    -- 37-field KCRITR schema
    ...
);
```

Key rules:
- Raw storage tables are append-only (immutable)
- Reconstruction tables can be rebuilt from raw data
- Extraction log tracks all data lineage

### File Organization

```
scripts/              # Core game logic (GDScript)
scenes/               # Godot scene files
maps/                 # Map JSON files
Defs/                 # Game definition files (JSON)
docs/                 # Game and platform documentation
tests/                # Godot test scripts
packages/             # TypeScript shared packages
apps/                 # Deployable applications
api/                  # Backend API
axiom-esports-data/   # Analytics pipeline
  analytics/          # Python analytics modules
  extraction/         # Data extraction pipeline
  infrastructure/     # Docker, database migrations
  visualization/      # SATOR Square React/D3/WebGL
  api/                # FastAPI routes
  docs/               # Analytics documentation
```

## Testing

### Determinism Tests (GDScript)

Always run determinism tests before submitting game changes:

```bash
# In Godot, run tests/test_determinism.tscn
# All tests should pass
```

### TypeScript Tests

```bash
npm run test:firewall    # Firewall enforcement tests
npm run validate:schema  # Schema validation
```

### Python Analytics Tests

```bash
cd axiom-esports-data/analytics
python -m pytest tests/     # Analytics unit tests
```

### Manual Testing

1. Run a full match
2. Save replay
3. Load replay and verify it matches
4. Test with different seeds
5. Verify UI updates correctly

## Documentation

Update relevant docs:
- `docs/architecture.md` — System design changes
- `docs/FIREWALL_POLICY.md` — Data classification changes
- `docs/map_format.md` — Map format changes
- `docs/agents.md` — Agent behavior changes
- `docs/replay.md` — Replay system changes
- `README.md` — User-facing changes
- `axiom-esports-data/docs/DATA_DICTIONARY.md` — Analytics schema changes
- `axiom-esports-data/docs/SATOR_ARCHITECTURE.md` — Visualization changes
- `axiom-esports-data/docs/CONFIDENCE_TIERS.md` — Confidence tier changes
- `axiom-esports-data/docs/EXTRACTION_EPOCHS.md` — Extraction pipeline changes

## AI-Assisted Development

SATOR includes a comprehensive prompting guide for AI-assisted development.
See **[.github/SATOR-COPILOT-PROMPTS.md](.github/SATOR-COPILOT-PROMPTS.md)** for:
- Context-setting prompts for each component
- Task-specific templates
- Validation and review prompts
- Emergency / debugging prompts

RadiantX also includes three specialized custom agents:
- **Agent 006** — Backend Architecture & Infrastructure
- **Agent 007** — Game Development & GDScript
- **Agent 47** — Frontend UI/UX & Accessibility

See [docs/custom-agents.md](docs/custom-agents.md) for details.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Open a GitHub Issue with the "question" label.

## Recognition

Contributors will be acknowledged in release notes and the README.

Thank you for helping make SATOR better!
