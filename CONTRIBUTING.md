# Contributing to SATOR / RadiantX

Thank you for your interest in contributing to SATOR!

## Project Philosophy

SATOR is a **two-part esports simulation platform**:
1. **RadiantX** — An offline, deterministic tactical FPS simulation game (Godot 4 / GDScript)
2. **SATOR Web** — An online public statistics platform (TypeScript, in development)

All contributions must respect:

1. **Determinism First**: All simulation logic must be deterministic
2. **Firewall Enforced**: Game-internal data must never reach the web platform
3. **Offline Capable**: Game requires no internet connectivity
4. **Windows Primary**: Optimize for Windows, though cross-platform is welcome
5. **Simulation Heavy**: Focus on tactical depth, not graphics

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

### GDScript Style

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

### TypeScript Style

```typescript
// Use strict mode
import type { Statistics } from '@sator/stats-schema';

// Always sanitize game data before sending to API
import { FantasyDataFilter } from '@sator/data-partition-lib';
const safe = FantasyDataFilter.sanitizeForWeb(rawData);
```

### File Organization

```
scripts/        # Core game logic (GDScript)
scenes/         # Godot scene files
maps/           # Map JSON files
docs/           # Documentation
tests/          # Godot test scripts
packages/       # TypeScript shared packages
apps/           # Deployable applications
api/            # Backend API
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
