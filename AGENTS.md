# AGENTS.md — SATOR / RadiantX Project Guide

This document provides essential information for AI coding agents working on the SATOR esports simulation platform. SATOR is a complex multi-component project with strict architectural boundaries and coding conventions.

---

## Project Overview

**SATOR** (also known as **RadiantX**) is a three-part esports simulation and analytics platform:

1. **RadiantX** — An offline, deterministic tactical FPS simulation game built with Godot 4 and GDScript
2. **Axiom Esports Data** — A tactical FPS analytics pipeline with SATOR Square 5-layer visualization (Python + React/TypeScript/D3/WebGL)
3. **SATOR Web** — An online public statistics platform (TypeScript/HTML/Tailwind CSS)

### Key Characteristics

- **Deterministic Simulation**: 20 TPS fixed timestep, seeded RNG for reproducible matches
- **Data Partition Firewall**: Strict boundary preventing game-internal data from reaching the public web
- **Dual-Storage Protocol**: Immutable raw data + calculated reconstruction data
- **Overfitting Guardrails**: Temporal train/test wall, adversarial validation, confidence weighting
- **37-field KCRITR Schema**: Comprehensive player performance database
- **SATOR Square Visualization**: 5-layer palindromic match analysis (D3.js + WebGL)

---

## Repository Structure

```
/
├── website/                    # Static website (HTML/CSS/JS/Tailwind)
│   ├── index.html             # Main entry point
│   ├── src/style.css          # Custom styles
│   ├── system/                # Core system files
│   └── package.json           # Node dependencies (Tailwind, PostCSS)
│
├── simulation-game/           # Godot 4 game project
│   ├── project.godot          # Godot project configuration
│   ├── scripts/               # GDScript game logic
│   │   ├── Main.gd           # Entry point
│   │   ├── MatchEngine.gd    # 20 TPS simulation loop
│   │   ├── Agent.gd          # Agent AI with belief system
│   │   ├── Data/             # 22 data type definitions
│   │   └── Sim/              # Combat resolution (6 files)
│   ├── scenes/                # Godot scene files
│   ├── maps/                  # JSON map definitions
│   ├── Defs/                  # Game definition files (JSON)
│   ├── tests/                 # GDScript determinism tests
│   └── tactical-fps-sim-core-updated/  # C# simulation core
│
├── shared/                    # Shared components
│   ├── axiom-esports-data/   # Python analytics pipeline
│   │   ├── extraction/       # VLR.gg scraping pipeline
│   │   ├── analytics/        # SimRating, RAR, investment grading
│   │   ├── visualization/    # SATOR Square React/D3/WebGL
│   │   ├── api/              # FastAPI REST service
│   │   ├── infrastructure/   # Docker, PostgreSQL migrations
│   │   ├── scripts/          # CLI operational tools
│   │   └── config/           # Static configuration
│   │
│   ├── packages/             # TypeScript shared packages
│   │   ├── stats-schema/     # Public stats type definitions
│   │   └── data-partition-lib/  # Firewall enforcement library
│   │
│   ├── apps/                 # Application placeholders (Phase 2+)
│   ├── api/                  # API placeholder (Phase 3+)
│   └── docs/                 # Project documentation
│
├── .github/workflows/        # CI/CD workflows
├── package.json              # Root npm workspace configuration
├── vercel.json               # Vercel deployment config
└── AGENTS.md                 # This file
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Game Engine** | Godot 4.x |
| **Game Language** | GDScript |
| **Simulation Core** | C# (.NET) |
| **Analytics** | Python 3.11+ |
| **Analytics Libraries** | pandas, scikit-learn, numpy, FastAPI |
| **Database** | PostgreSQL 15 + TimescaleDB |
| **Web Frontend** | HTML5, Tailwind CSS, vanilla JavaScript |
| **Visualization** | React 18, TypeScript, D3.js, WebGL/Three.js |
| **Containerization** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |

---

## Build and Development Commands

### Website (Static)

```bash
cd website
npm install      # Install Tailwind, PostCSS dependencies
npm run build    # Build CSS (Tailwind compilation)
```

The website is deployed to GitHub Pages via `.github/workflows/static.yml`.

### RadiantX Game (Godot)

```bash
# Open project.godot in Godot 4.x Editor
# Press F5 to run
# Or use Godot CLI:
godot --path simulation-game --scene scenes/Main.tscn
```

### Axiom Esports Data (Python)

```bash
cd shared/axiom-esports-data

# Database setup
docker-compose -f infrastructure/docker-compose.yml up -d
psql $DATABASE_URL -f infrastructure/migrations/001_initial_schema.sql

# Extraction pipeline
cd extraction
pip install -r requirements.txt
python src/scrapers/epoch_harvester.py --mode=delta

# Analytics
cd ../analytics
pytest tests/ -v
```

### TypeScript Packages

```bash
# Root level (workspaces)
npm install
npm run build              # Build all packages
npm run typecheck          # Type check all packages
npm run test:firewall      # Run firewall enforcement tests
npm run validate:schema    # Validate stats schema
```

---

## Code Style Guidelines

### GDScript (Game)

- **Indentation**: Tabs only (not spaces)
- **Naming**: `snake_case` for variables/functions, `PascalCase` for classes
- **Determinism Rules**:
  - Only use seeded RNG — never use `randf()` or `randi()` directly
  - Fixed timestep (20 TPS, 50ms) — never use delta-time in simulation logic
  - Consistent ordering — process agents/actions in the same order every tick

```gdscript
# Example
global class_name MatchEngine

func calculate_damage(attacker: Agent, target: Agent) -> float:
	var base_damage = 25.0
	return base_damage
```

### Python (Analytics)

- Follow PEP 8 style
- Use type hints for all function signatures
- **Overfitting Guardrails**:
  - All data must pass through `integrity_checker.py` before analytics
  - Use `temporal_wall.py` to enforce train/test temporal splits
  - Use `confidence_sampler.py` for confidence-weighted calculations

```python
from typing import Dict, List, Optional

def calculate_simrating(
    player_stats: Dict[str, float],
    role: str,
    confidence: float = 1.0
) -> float:
    """Calculate 5-component SimRating for a player."""
    pass
```

### TypeScript (Packages/Web)

- Strict TypeScript mode enabled
- **Firewall Enforcement**: Always sanitize game data before sending to API

```typescript
import { FantasyDataFilter } from '@sator/data-partition-lib';
const safe = FantasyDataFilter.sanitizeForWeb(rawData);
```

### SQL (Migrations)

- Numbered migration files: `001_`, `002_`, etc.
- Always include rollback (DOWN) migration
- Use `snake_case` for table and column names

---

## Testing Instructions

### GDScript Determinism Tests

```bash
# In Godot Editor, run:
simulation-game/tests/test_determinism.tscn
# All tests must pass before submitting game changes
```

### Python Analytics Tests

```bash
cd shared/axiom-esports-data/analytics
pytest tests/ -v

# Required coverage:
# - test_schema_validation.py — 37-field KCRITR completeness
# - test_integral_checker.py — SHA-256 checksums
# - test_temporal_wall.py — no future data in training
# - test_overfitting_guard.py — adversarial detection
```

### TypeScript Tests

```bash
# Firewall tests
npm run test:firewall

# Schema validation
npm run validate:schema

# Type checking
npm run typecheck
```

### Test Coverage Requirements

| Component | Requirement |
|-----------|-------------|
| GDScript | Determinism verification — same seed produces same output |
| Python | HLTV correlation r > 0.85, duplicate rate < 0.01% |
| Firewall | All `GAME_ONLY_FIELDS` stripped by `sanitizeForWeb()` |
| Schema | No unexpected fields in public types |

---

## Security Considerations

### Data Partition Firewall

The firewall prevents game-internal fields from reaching the public web platform:

**GAME-ONLY Fields (blocked)**:
- `internalAgentState` — AI decision tree
- `radarData` — Real-time position feed
- `detailedReplayFrameData` — Per-tick simulation frames
- `simulationTick` — Engine internal counter
- `seedValue` — RNG seed
- `visionConeData` — Agent vision state
- `smokeTickData` — Smoke utility state
- `recoilPattern` — Per-weapon recoil data

**Enforcement Points**:
1. Game extraction (`LiveSeasonModule.gd`)
2. API middleware filter (TypeScript)
3. Web schema validation (`stats-schema`)
4. CI/CD automated testing

### Critical Rules

- Never commit `.env` files — use `.env.example` as template
- Never commit model files (`.pkl`, `.joblib`) — gitignored
- No hardcoded player IDs in test files
- All firewall changes require `@hvrryh-web` approval (CODEOWNERS)

---

## Deployment Process

### GitHub Pages (Website)

Triggered on push to `main` branch:
```yaml
# .github/workflows/static.yml
- Uploads ./website folder to GitHub Pages
```

### Vercel (Alternative)

Configured in `vercel.json` with static build settings.

### Axiom Data Pipeline

```bash
# Daily extraction (scheduled CI)
python src/scrapers/epoch_harvester.py --mode=delta

# Weekly analytics refresh
python scripts/weekly_analytics_refresh.py

# Monthly full harvest
python scripts/monthly_full_harvest.py
```

---

## Documentation Index

| Document | Location | Purpose |
|----------|----------|---------|
| Quick Start | `shared/docs/quick_start.md` | Getting started guide |
| Architecture | `shared/docs/architecture.md` | System design overview |
| Agent Behavior | `shared/docs/agents.md` | AI agent documentation |
| Map Format | `shared/docs/map_format.md` | JSON map specification |
| Replay System | `shared/docs/replay.md` | Match replay guide |
| Firewall Policy | `shared/docs/FIREWALL_POLICY.md` | Data partition rules |
| Branch Strategy | `shared/docs/BRANCH_STRATEGY.md` | Git workflow |
| AXIOM Guide | `shared/axiom-esports-data/AXIOM.md` | AI agent operational guide |
| Data Dictionary | `shared/axiom-esports-data/docs/DATA_DICTIONARY.md` | 37-field KCRITR schema |
| SATOR Architecture | `shared/axiom-esports-data/docs/SATOR_ARCHITECTURE.md` | 5-layer visualization spec |

---

## Environment Variables

Copy `shared/axiom-esports-data/.env.example` to `.env` and configure:

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/axiom_esports
VLR_RATE_LIMIT=2.0
HLTV_API_KEY=optional_for_validation
GRID_API_KEY=optional_partnership
GITHUB_TOKEN=for_actions
DATA_RETENTION_DAYS=730
```

**Never commit `.env` files to version control.**

---

## Common Tasks for AI Agents

### Adding a New Data Source

1. Create scraper in `shared/axiom-esports-data/extraction/src/scrapers/`
2. Add parser in `shared/axiom-esports-data/extraction/src/parsers/`
3. Extend `extraction_bridge.py` to map schema to KCRITR fields
4. Add cross-reference validation in `validation_crossref.py`
5. Update `shared/axiom-esports-data/docs/DATA_DICTIONARY.md`

### Modifying Game Simulation

1. Ensure determinism — use seeded RNG only
2. Update `MatchEngine.gd` or relevant subsystem
3. Run determinism tests: `test_determinism.tscn`
4. Update documentation in `shared/docs/`

### Adding Public Statistics

1. Determine if field is game-internal (see FIREWALL_POLICY.md decision tree)
2. If public: add to `shared/packages/stats-schema/src/types/`
3. If game-only: add to `FantasyDataFilter.GAME_ONLY_FIELDS`
4. Run `npm run test:firewall` and `npm run validate:schema`
5. Update firewall documentation

### Database Migrations

```bash
cd shared/axiom-esports-data/infrastructure
# Apply in order:
psql $DATABASE_URL -f migrations/001_initial_schema.sql
psql $DATABASE_URL -f migrations/002_sator_layers.sql
# ... etc
```

---

## License

- **RadiantX Game**: MIT License
- **Axiom Esports Data**: CC BY-NC 4.0 (Non-commercial use with attribution)

---

*Last updated: 2026-03-04*
