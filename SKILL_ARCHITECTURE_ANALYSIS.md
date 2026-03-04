# SATOR Project Skill Architecture Analysis

## Executive Summary

The SATOR/RadiantX project is a multi-component esports analytics platform requiring specialized Kimi agent skills. This document maps project components to required skills, defines dependencies, and provides a recommended skill file structure.

**Project Scale:**
- 6 major components
- 4 programming languages (GDScript, C#, Python, TypeScript)
- 3 deployment targets (Render, Vercel, Supabase)
- 22 data type definitions, 5-layer visualization system
- 3-epoch temporal data extraction pipeline

---

## 1. Component-to-Skill Mapping

### 1.1 Simulation Game (Godot 4)

| Project Element | Technology | Required Skill |
|-----------------|------------|----------------|
| `simulation-game/scripts/*.gd` | GDScript | `sator-godot-dev` |
| `simulation-game/tactical-fps-sim-core-updated/*.cs` | C# | `sator-godot-dev` |
| `simulation-game/Defs/*.json` | Game data | `sator-simulation` |
| MatchEngine, Agent, DuelResolver | Deterministic sim | `sator-simulation` |
| 20 TPS tick system | Fixed timestep | `sator-simulation` |
| Seeded RNG | Determinism | `sator-simulation` |

**Key Capabilities Needed:**
- Godot 4 scene/script management
- GDScript coding conventions (tabs, snake_case)
- Deterministic simulation patterns
- Combat resolution systems
- EventLog for replay functionality

### 1.2 Python Analytics Pipeline

| Project Element | Technology | Required Skill |
|-----------------|------------|----------------|
| `extraction/src/scrapers/` | aiohttp, async | `sator-extraction` |
| `extraction/src/parsers/` | BeautifulSoup | `sator-extraction` |
| `pipeline/orchestrator.py` | Async pipeline | `sator-python-pipeline` |
| `analytics/src/simrating/` | Statistics | `sator-analytics` |
| `analytics/src/rar/` | RAR calculations | `sator-analytics` |
| `infrastructure/migrations/` | PostgreSQL | `sator-python-pipeline` |

**Key Capabilities Needed:**
- Async Python patterns (aiohttp, asyncpg)
- Web scraping with rate limiting
- ETL pipeline orchestration
- PostgreSQL with asyncpg
- Temporal epoch data management

### 1.3 FastAPI Backend

| Project Element | Technology | Required Skill |
|-----------------|------------|----------------|
| `api/main.py` | FastAPI | `sator-fastapi-backend` |
| `api/src/routes/` | API endpoints | `sator-fastapi-backend` |
| `api/src/middleware/firewall.py` | Middleware | `sator-data-firewall` |
| `api/src/schemas/` | Pydantic | `sator-fastapi-backend` |
| `api/Dockerfile` | Containerization | `sator-deployment` |

**Key Capabilities Needed:**
- FastAPI async patterns
- Pydantic schema validation
- Middleware development
- PostgreSQL connection pooling
- Health checks and monitoring

### 1.4 React TypeScript Frontend

| Project Element | Technology | Required Skill |
|-----------------|------------|----------------|
| `apps/sator-web/src/` | React 18 | `sator-react-frontend` |
| `apps/sator-web/src/services/api.ts` | Axios | `sator-react-frontend` |
| `visualization/sator-square/` | D3.js/WebGL | `sator-sator-square` |
| `packages/stats-schema/` | Type definitions | `sator-react-frontend` |
| `packages/data-partition-lib/` | Firewall lib | `sator-data-firewall` |

**Key Capabilities Needed:**
- Vite + React 18 + TypeScript
- Tailwind CSS styling
- TanStack Query data fetching
- D3.js visualization
- WebGL/GLSL shaders

### 1.5 DevOps/Deployment

| Project Element | Technology | Required Skill |
|-----------------|------------|----------------|
| `.github/workflows/` | GitHub Actions | `sator-deployment` |
| `api/Dockerfile` | Docker | `sator-deployment` |
| `vercel.json` | Vercel | `sator-deployment` |
| `infrastructure/docker-compose.yml` | Docker Compose | `sator-deployment` |

**Key Capabilities Needed:**
- Free-tier deployment optimization
- Render (FastAPI) deployment
- Vercel (React) deployment
- GitHub Actions CI/CD
- Docker containerization

---

## 2. Skill Dependencies

```
                    ┌─────────────────────────────────────┐
                    │         sator-end-to-end            │
                    │      (Full Stack Integration)       │
                    └──────────────┬──────────────────────┘
                                   │ uses
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
           ▼                       ▼                       ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│ sator-simulation  │  │ sator-python-     │  │ sator-react-      │
│    (Godot/C#)     │  │   pipeline        │  │   frontend        │
└─────────┬─────────┘  └─────────┬─────────┘  └─────────┬─────────┘
          │                      │                      │
          │ extends              │ extends              │ extends
          │                      │                      │
          ▼                      ▼                      ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│  sator-godot-dev  │  │ sator-extraction  │  │ sator-sator-square│
│   (Base: Godot)   │  │  (Base: Scraping) │  │  (Base: D3/WebGL) │
└───────────────────┘  └─────────┬─────────┘  └───────────────────┘
                                 │
                                 │ uses
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
          ┌───────────────────┐    ┌───────────────────┐
          │  sator-analytics  │    │ sator-fastapi-    │
          │ (SimRating/RAR)   │    │    backend        │
          └─────────┬─────────┘    └─────────┬─────────┘
                    │                        │
                    └──────────┬─────────────┘
                               │ both use
                               ▼
                    ┌───────────────────┐
                    │  sator-data-      │
                    │    firewall       │
                    │ (Security Layer)  │
                    └─────────┬─────────┘
                              │
                              │ uses
                              ▼
                    ┌───────────────────┐
                    │  sator-deployment │
                    │ (DevOps/Deploy)   │
                    └───────────────────┘
```

### Dependency Matrix

| Skill | Depends On | Used By |
|-------|------------|---------|
| `sator-godot-dev` | - | `sator-simulation` |
| `sator-python-pipeline` | - | `sator-extraction`, `sator-analytics` |
| `sator-react-frontend` | - | `sator-sator-square` |
| `sator-fastapi-backend` | - | `sator-data-firewall`, `sator-python-pipeline` |
| `sator-simulation` | `sator-godot-dev` | `sator-end-to-end` |
| `sator-extraction` | `sator-python-pipeline` | `sator-end-to-end` |
| `sator-analytics` | `sator-python-pipeline` | `sator-end-to-end` |
| `sator-sator-square` | `sator-react-frontend` | `sator-end-to-end` |
| `sator-data-firewall` | `sator-fastapi-backend` | `sator-end-to-end` |
| `sator-deployment` | - | ALL (for deployment tasks) |
| `sator-end-to-end` | ALL above | - |

---

## 3. Skill Hierarchy

### 3.1 Base Skills (Foundation Layer)

These skills provide core technology capabilities independent of SATOR domain logic.

#### `sator-godot-dev`
- **Purpose:** Godot 4 engine development with GDScript and C#
- **Scope:** Scene management, scripting, deterministic patterns
- **Independence:** Fully independent

#### `sator-python-pipeline`
- **Purpose:** Async Python data pipeline development
- **Scope:** Asyncio, aiohttp, asyncpg, ETL patterns
- **Independence:** Fully independent

#### `sator-react-frontend`
- **Purpose:** React TypeScript frontend development
- **Scope:** Vite, Tailwind, TanStack Query, API integration
- **Independence:** Fully independent

#### `sator-fastapi-backend`
- **Purpose:** FastAPI async backend development
- **Scope:** FastAPI, Pydantic, asyncpg, middleware
- **Independence:** Fully independent

#### `sator-deployment`
- **Purpose:** Free-tier deployment automation
- **Scope:** Render, Vercel, GitHub Actions, Docker
- **Independence:** Fully independent

### 3.2 Specialized Skills (Domain Layer)

These skills build on base skills to provide SATOR-specific capabilities.

#### `sator-simulation`
- **Extends:** `sator-godot-dev`
- **Domain:** Deterministic tactical FPS simulation
- **Unique:** 20 TPS, seeded RNG, combat resolution

#### `sator-extraction`
- **Extends:** `sator-python-pipeline`
- **Domain:** VLR.gg web scraping with epoch management
- **Unique:** 3-epoch temporal extraction, rate limiting

#### `sator-analytics`
- **Extends:** `sator-python-pipeline`
- **Domain:** SimRating and RAR calculations
- **Unique:** Z-score normalization, confidence tiers

#### `sator-sator-square`
- **Extends:** `sator-react-frontend`
- **Domain:** 5-layer SATOR square visualization
- **Unique:** D3.js + WebGL, GLSL shaders, spatial data

#### `sator-data-firewall`
- **Extends:** `sator-fastapi-backend`
- **Domain:** Data partition enforcement
- **Unique:** `FantasyDataFilter`, `GAME_ONLY_FIELDS`

### 3.3 Integration Skills (Orchestration Layer)

These skills coordinate multiple specialized skills for end-to-end workflows.

#### `sator-end-to-end`
- **Uses:** All specialized skills
- **Purpose:** Full-stack feature development across all components
- **Scope:** Cross-component changes, API contracts, data flow

---

## 4. Skill Interfaces

### 4.1 Input/Output Specifications

#### `sator-godot-dev`
```yaml
Inputs:
  - task: "create|modify|debug"
  - component: "MatchEngine|Agent|DuelResolver|..."
  - scene_path: string (optional)
  
Outputs:
  - .gd files (GDScript)
  - .cs files (C#)
  - .tscn files (scenes)
  
Constraints:
  - Use tabs for indentation
  - snake_case for variables/functions
  - PascalCase for classes
  - Maintain determinism (seeded RNG only)
```

#### `sator-python-pipeline`
```yaml
Inputs:
  - task: "extract|transform|load|orchestrate"
  - source: "vlr_gg|manual|api"
  - epochs: [1, 2, 3] (optional)
  
Outputs:
  - Python async modules
  - SQL migrations
  - Pipeline configuration
  
Constraints:
  - Must use async/await patterns
  - Rate limiting required for scraping
  - PostgreSQL with asyncpg
```

#### `sator-extraction`
```yaml
Inputs:
  - epoch: 1|2|3
  - mode: "delta|full|backfill"
  - match_ids: string[] (optional)
  
Outputs:
  - Raw HTML files
  - Checksums
  - Extraction logs
  
Constraints:
  - Must respect KnownRecordRegistry
  - Ethical rate limiting (configurable)
  - 3-epoch temporal boundaries
```

#### `sator-analytics`
```yaml
Inputs:
  - metric: "SimRating|RAR|InvestmentGrade"
  - player_id: string
  - season: string (optional)
  
Outputs:
  - Calculated metrics
  - Z-scores
  - Confidence tiers
  
Constraints:
  - Use adjusted_kill_value, not raw ACS
  - Temporal wall for train/test separation
  - Confidence floor per epoch
```

#### `sator-fastapi-backend`
```yaml
Inputs:
  - route: string
  - method: "GET|POST|PUT|DELETE"
  - schema: Pydantic model
  
Outputs:
  - FastAPI route handlers
  - Pydantic schemas
  - Middleware
  
Constraints:
  - Must apply firewall middleware
  - Health checks required
  - Async database operations
```

#### `sator-data-firewall`
```yaml
Inputs:
  - data: any (game data)
  - direction: "game_to_web|web_to_game"
  
Outputs:
  - Sanitized data (game_to_web)
  - Validation result (web_to_game)
  
Constraints:
  - Must strip GAME_ONLY_FIELDS
  - Fail closed on validation errors
  - CODEOWNERS review required for changes
```

#### `sator-react-frontend`
```yaml
Inputs:
  - page: string
  - component: string
  - data_requirements: string[]
  
Outputs:
  - React components
  - API service functions
  - TypeScript types
  
Constraints:
  - Use @sator/stats-schema types
  - Never import game code
  - Tailwind for styling
```

#### `sator-sator-square`
```yaml
Inputs:
  - layer: "SATOR|OPERA|TENET|AREPO|ROTAS"
  - match_id: string
  - round_number: number
  
Outputs:
  - React layer components
  - GLSL shaders
  - Spatial data hooks
  
Constraints:
  - D3.js for SVG layers (1, 3, 4)
  - WebGL for Canvas layers (2, 5)
  - Target 60 FPS
```

#### `sator-deployment`
```yaml
Inputs:
  - target: "render|vercel|github_pages"
  - component: "api|web|pipeline"
  - environment: "dev|staging|prod"
  
Outputs:
  - GitHub Actions workflows
  - Dockerfiles
  - Deployment configs
  
Constraints:
  - Free-tier optimization
  - Cold start mitigation
  - Health check endpoints
```

---

## 5. Recommended Skill File Structure

```
.agents/skills/
├── sator-godot-dev/
│   ├── SKILL.md
│   ├── templates/
│   │   ├── MatchEngine.gd.template
│   │   ├── Agent.gd.template
│   │   ├── project.godot.template
│   │   └── CSharp_SimCore.csproj.template
│   ├── scripts/
│   │   ├── validate_determinism.py
│   │   └── generate_data_types.py
│   └── examples/
│       ├── basic_agent_ai.md
│       ├── combat_resolution.md
│       └── deterministic_rng.md
│
├── sator-python-pipeline/
│   ├── SKILL.md
│   ├── templates/
│   │   ├── orchestrator.py.template
│   │   ├── migration.sql.template
│   │   └── async_client.py.template
│   ├── scripts/
│   │   ├── run_pipeline.py
│   │   └── validate_schema.py
│   └── examples/
│       ├── epoch_extraction.md
│       ├── async_patterns.md
│       └── database_migrations.md
│
├── sator-extraction/
│   ├── SKILL.md
│   ├── templates/
│   │   ├── epoch_harvester.py.template
│   │   ├── vlr_client.py.template
│   │   └── match_parser.py.template
│   ├── scripts/
│   │   └── rate_limit_check.py
│   └── examples/
│       ├── ethical_scraping.md
│       ├── epoch_management.md
│       └── registry_integration.md
│
├── sator-analytics/
│   ├── SKILL.md
│   ├── templates/
│   │   ├── simrating_calculator.py.template
│   │   ├── rar_decomposer.py.template
│   │   └── investment_grader.py.template
│   ├── scripts/
│   │   └── validate_metrics.py
│   └── examples/
│       ├── simrating_calculation.md
│       ├── rar_methodology.md
│       └── confidence_tiers.md
│
├── sator-fastapi-backend/
│   ├── SKILL.md
│   ├── templates/
│   │   ├── main.py.template
│   │   ├── routes.py.template
│   │   ├── middleware.py.template
│   │   └── schema.py.template
│   ├── scripts/
│   │   └── test_endpoints.py
│   └── examples/
│       ├── async_endpoints.md
│       ├── health_checks.md
│       └── error_handling.md
│
├── sator-data-firewall/
│   ├── SKILL.md
│   ├── templates/
│   │   ├── FantasyDataFilter.ts.template
│   │   ├── firewall_middleware.py.template
│   │   └── GAME_ONLY_FIELDS.json
│   ├── scripts/
│   │   └── audit_fields.py
│   └── examples/
│       ├── data_classification.md
│       ├── enforcement_points.md
│       └── violation_response.md
│
├── sator-react-frontend/
│   ├── SKILL.md
│   ├── templates/
│   │   ├── App.tsx.template
│   │   ├── api.ts.template
│   │   ├── Page.tsx.template
│   │   └── Component.tsx.template
│   ├── scripts/
│   │   └── check_imports.py
│   └── examples/
│       ├── tanstack_query.md
│       ├── tailwind_patterns.md
│       └── type_safety.md
│
├── sator-sator-square/
│   ├── SKILL.md
│   ├── templates/
│   │   ├── SatorLayer.tsx.template
│   │   ├── OperaLayer.tsx.template
│   │   ├── fog.frag.template
│   │   └── dust.vert.template
│   ├── scripts/
│   │   └── validate_webgl.py
│   └── examples/
│       ├── d3_visualization.md
│   │   ├── webgl_shaders.md
│   │   └── layer_composition.md
│
├── sator-simulation/
│   ├── SKILL.md
│   ├── templates/
│   │   ├── Simulator.cs.template
│   │   ├── CombatResolver.gd.template
│   │   └── EventLog.gd.template
│   ├── scripts/
│   │   └── test_determinism.py
│   └── examples/
│       ├── tick_system.md
│   │   ├── combat_resolution.md
│   │   └── replay_system.md
│
├── sator-deployment/
│   ├── SKILL.md
│   ├── templates/
│   │   ├── github-actions.yml.template
│   │   ├── render.yaml.template
│   │   ├── vercel.json.template
│   │   └── Dockerfile.template
│   ├── scripts/
│   │   └── deploy_check.py
│   └── examples/
│       ├── render_deploy.md
│       ├── vercel_deploy.md
│       └── github_actions.md
│
└── sator-end-to-end/
    ├── SKILL.md
    ├── templates/
    │   ├── feature_spec.md.template
    │   └── api_contract.yaml.template
    ├── scripts/
    │   └── full_stack_test.py
    └── examples/
        ├── adding_a_stat.md
        ├── cross_component_feature.md
        └── data_flow_integration.md
```

---

## 6. Priority Ranking

### Critical (P0) - Required for Core Development

| Rank | Skill | Justification |
|------|-------|---------------|
| 1 | `sator-data-firewall` | Security-critical; prevents data leakage between game and web |
| 2 | `sator-godot-dev` | Core game development; affects all simulation work |
| 3 | `sator-python-pipeline` | Data pipeline foundation; affects all analytics |

### High (P1) - Required for Feature Development

| Rank | Skill | Justification |
|------|-------|---------------|
| 4 | `sator-extraction` | Data source for entire platform |
| 5 | `sator-fastapi-backend` | API layer for web platform |
| 6 | `sator-react-frontend` | Web platform UI |

### Medium (P2) - Specialized Capabilities

| Rank | Skill | Justification |
|------|-------|---------------|
| 7 | `sator-analytics` | Required for SimRating/RAR features |
| 8 | `sator-sator-square` | Required for visualization features |
| 9 | `sator-simulation` | Required for advanced game features |

### Lower (P3) - Operational

| Rank | Skill | Justification |
|------|-------|---------------|
| 10 | `sator-deployment` | Required for production releases |
| 11 | `sator-end-to-end` | Required for complex cross-component features |

---

## 7. Skill Template Examples

### 7.1 SKILL.md Template Structure

Each skill should follow this structure based on Azure skill patterns:

```markdown
---
name: sator-{skill-name}
description: "Clear description of when to use this skill. USE FOR: trigger phrases. DO NOT USE FOR: exclusions."
license: MIT
metadata:
  author: SATOR Team
  version: "1.0.0"
---

# Skill Name

> **AUTHORITATIVE GUIDANCE — MANDATORY COMPLIANCE**
> This document is the official source for [capability].

## Triggers

Activate this skill when user wants to:
- Trigger condition 1
- Trigger condition 2

## Rules

1. Rule one
2. Rule two

## WHEN to Use / DO NOT USE

| USE FOR | DO NOT USE FOR |
|---------|----------------|
| Valid use case 1 | Invalid use case 1 |
| Valid use case 2 | Invalid use case 2 |

## Required Tools/Configuration

- Tool 1: purpose
- Tool 2: purpose

## Example Workflows

### Example 1: Common Task

```bash
# Step-by-step commands
```

## References

- Link to templates
- Link to examples
```

### 7.2 Example: sator-data-firewall/SKILL.md

```markdown
---
name: sator-data-firewall
description: "Enforce SATOR data partition firewall between game simulation and web platform. USE FOR: data sanitization, GAME_ONLY_FIELDS management, firewall middleware, data classification. DO NOT USE FOR: general API security, authentication, non-SATOR projects."
license: MIT
metadata:
  author: SATOR Team
  version: "1.0.0"
---

# SATOR Data Firewall

> **CRITICAL SECURITY COMPONENT**
> The firewall prevents game-internal data from reaching the public web platform.
> Any modification requires CODEOWNERS approval from @hvrryh-web.

## Triggers

Activate this skill when:
- Adding new data fields that cross game/web boundary
- Implementing data sanitization
- Modifying GAME_ONLY_FIELDS
- Creating API middleware
- Investigating data leakage

## Rules

1. **Fail closed** - Deny by default on validation errors
2. **Deep clone** - Never mutate original game data
3. **CODEOWNERS** - Changes require @hvrryh-web approval
4. **Four enforcement points** - All must pass:
   - Point 1: Game Extraction (LiveSeasonModule.gd)
   - Point 2: API Middleware Filter (TypeScript)
   - Point 3: Web Schema Validation (TypeScript)
   - Point 4: CI/CD Testing

## WHEN to Use / DO NOT USE

| USE FOR | DO NOT USE FOR |
|---------|----------------|
| Sanitizing game data for web | General API authentication |
| Validating web input | Database encryption |
| Managing GAME_ONLY_FIELDS | Network security |
| Data classification decisions | User authorization |
| Firewall middleware | HTTPS/TLS configuration |

## Required Tools/Configuration

- `packages/data-partition-lib/src/FantasyDataFilter.ts`
- `docs/FIREWALL_POLICY.md`
- `.github/CODEOWNERS`

## Example Workflows

### Add a New Game-Only Field

```typescript
// Step 1: Add to GAME_ONLY_FIELDS
static GAME_ONLY_FIELDS = new Set([
  // ... existing fields
  'newInternalField',  // Add here
]);
```

### Sanitize Data for Web

```typescript
import { FantasyDataFilter } from '@sator/data-partition-lib';

const sanitized = FantasyDataFilter.sanitizeForWeb(gameData);
// sanitized now safe for API response
```

### Validate Incoming Data

```typescript
// In API middleware
try {
  FantasyDataFilter.validateWebInput(req.body);
  next();
} catch (err) {
  res.status(400).json({ error: 'Firewall: ' + err.message });
}
```

## Violation Response Procedure

| Severity | Condition | Action |
|----------|-----------|--------|
| Critical | GAME_ONLY_FIELDS in production DB | Immediate rollback; audit all deployments |
| High | Field leaks through API | Block deploy; fix middleware; re-run tests |
| Medium | Field in extraction but caught by middleware | Fix LiveSeasonModule; add regression test |
| Low | CI detects new unlisted field | Add to GAME_ONLY_FIELDS or schema |

## References

- [FIREWALL_POLICY.md](../../../shared/docs/FIREWALL_POLICY.md)
- [templates/FantasyDataFilter.ts.template](./templates/FantasyDataFilter.ts.template)
- [examples/data_classification.md](./examples/data_classification.md)
```

---

## 8. Implementation Roadmap

### Phase 1: Foundation (P0 Skills)
1. Create `sator-data-firewall` (security critical)
2. Create `sator-godot-dev` (game foundation)
3. Create `sator-python-pipeline` (data foundation)

### Phase 2: Core Platform (P1 Skills)
4. Create `sator-fastapi-backend`
5. Create `sator-react-frontend`
6. Create `sator-extraction`

### Phase 3: Specialization (P2 Skills)
7. Create `sator-analytics`
8. Create `sator-sator-square`
9. Create `sator-simulation`

### Phase 4: Operations (P3 Skills)
10. Create `sator-deployment`
11. Create `sator-end-to-end`

---

## 9. Maintenance Considerations

### Version Management
- Each skill has independent versioning
- Major versions for breaking changes
- Skills can reference compatible versions of dependencies

### Update Triggers
Skills should be updated when:
- New Godot version released → Update `sator-godot-dev`
- New Python async patterns → Update `sator-python-pipeline`
- New SATOR component added → Create new skill or extend existing
- Security vulnerability found → Update affected skills

### Testing Strategy
- Each skill has validation scripts in `scripts/`
- Integration tests in `sator-end-to-end`
- CI workflows test skill compliance

---

## Appendix A: Skill-to-File Mapping

| Skill | Primary Files |
|-------|---------------|
| `sator-godot-dev` | `simulation-game/**/*.gd`, `simulation-game/**/*.cs` |
| `sator-python-pipeline` | `shared/axiom-esports-data/pipeline/**/*.py`, `infrastructure/migrations/*.sql` |
| `sator-extraction` | `shared/axiom-esports-data/extraction/**/*.py` |
| `sator-analytics` | `shared/axiom-esports-data/analytics/**/*.py` |
| `sator-fastapi-backend` | `shared/axiom-esports-data/api/**/*.py` |
| `sator-data-firewall` | `shared/packages/data-partition-lib/**/*.ts`, `api/src/middleware/firewall.py` |
| `sator-react-frontend` | `shared/apps/sator-web/src/**/*.tsx`, `shared/packages/stats-schema/**/*.ts` |
| `sator-sator-square` | `shared/axiom-esports-data/visualization/sator-square/**/*.tsx` |
| `sator-simulation` | `simulation-game/scripts/Sim/**/*.gd`, `SimCore/**/*.cs` |
| `sator-deployment` | `.github/workflows/*.yml`, `**/Dockerfile`, `**/vercel.json` |
| `sator-end-to-end` | Cross-component coordination |

---

*Document Version: 1.0.0*
*Last Updated: 2026-03-04*
*Project: SATOR/RadiantX Esports Analytics Platform*
