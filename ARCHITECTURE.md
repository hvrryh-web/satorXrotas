# SATOR/RadiantX Platform Architecture

## Executive Summary

SATOR (also known as RadiantX) is a three-part esports simulation and analytics platform for professional Valorant and Counter-Strike esports. The platform combines deterministic game simulation, real-time data extraction, and advanced analytics with a branded web interface.

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SATOR PLATFORM ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────┐                                                     │
│  │   WEB PLATFORM      │  React 18 + TypeScript + Vite                       │
│  │   (Vercel)          │  Porcelain³ Design System                           │
│  │                     │  Quarterly Grid Navigation                          │
│  └──────────┬──────────┘                                                     │
│             │                                                                │
│  ┌──────────▼──────────┐                                                    │
│  │   API LAYER         │  FastAPI (Python)                                   │
│  │   (Render)          │  Data Partition Firewall                            │
│  │                     │  PostgreSQL via asyncpg                             │
│  └──────────┬──────────┘                                                     │
│             │                                                                │
│  ┌──────────▼──────────┐                                                    │
│  │   DATA LAYER        │  PostgreSQL 15 + TimescaleDB                        │
│  │   (Supabase)        │  Partitioned by game (CS/Valorant)                  │
│  │                     │  Dual storage protocol                              │
│  └──────────┬──────────┘                                                     │
│             │                                                                │
│  ┌──────────▼──────────┐                                                    │
│  │   PIPELINE LAYER    │  Python ETL + Coordinator                           │
│  │   (GitHub Actions)  │  CS + Valorant extractors                           │
│  │                     │  Job queue with conflict resolution                   │
│  └──────────┬──────────┘                                                     │
│             │                                                                │
│  ┌──────────▼──────────┐                                                    │
│  │   SIMULATION        │  Godot 4 Engine                                     │
│  │   (Local)           │  20 TPS deterministic                               │
│  │                     │  LiveSeasonModule export                            │
│  └─────────────────────┘                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Web Platform

**Location:** `shared/apps/sator-web/`

**Technology Stack:**
- React 18 with TypeScript
- Vite build tool
- Tailwind CSS
- TanStack Query for data fetching
- Recharts for data visualization
- React Router DOM for navigation

**Key Features:**
- Porcelain³ branded design system
- Quarterly grid navigation (4 + 1 hub)
- Expandable HelpHub with health dashboard
- 3D loading corridor animation
- Responsive design (mobile-first)
- SATOR Square 5-layer visualization system

**Pages:**
- `/` - Landing page with SATOR³ branding
- `/loading` - 3D corridor transition
- `/services` - Service selection dashboard
- `/analytics` - Advanced analytics hub
- `/stats` - Statistics reference
- `/info` - Documentation hub
- `/matches` - Match listings
- `/players` - Player directory

### 2. API Layer

**Location:** `shared/axiom-esports-data/api/`

**Technology Stack:**
- FastAPI (Python 3.11+)
- asyncpg for PostgreSQL
- Pydantic for validation
- Uvicorn ASGI server
- GZip compression middleware

**Security:**
- Data partition firewall middleware
- CORS configuration
- Request logging
- Health check endpoints (/health, /ready, /live)

**Endpoints:**
```
GET  /api/players          # List/search players
GET  /api/players/{id}     # Player details
GET  /api/matches          # List matches
GET  /api/matches/{id}     # Match details
GET  /api/analytics        # Analytics data
GET  /health               # Health check
GET  /ready                # Readiness check
GET  /live                 # Liveness check
GET  /metrics              # Prometheus metrics
GET  /docs                 # OpenAPI documentation (dev only)
GET  /redoc                # ReDoc documentation
```

### 3. Database Layer

**Location:** `shared/axiom-esports-data/infrastructure/migrations/`

**Technology:**
- PostgreSQL 15
- TimescaleDB extension for time-series data
- Partitioned tables by game (CS/Valorant)

**Schema Design:**
```
matches (parent)
├── matches_cs (partition)
└── matches_valorant (partition)

player_performance (parent)
├── player_performance_cs (partition)
└── player_performance_valorant (partition)
```

**Key Tables:**
- `player_performance` - 37-field KCRITR schema with match statistics
- `matches`, `matches_cs`, `matches_valorant` - Match metadata
- `teams`, `players` - Entity tables
- `tournaments` - Tournament information
- `raw_extractions` - Immutable source data
- `extraction_jobs` - Pipeline job queue
- `pipeline_alerts` - Monitoring alerts
- `staging_ingest_queue` - Central data staging

**Key Features:**
- 90-day chunk time intervals (TimescaleDB hypertables)
- Separation flag pattern (raw=0, reconstructed=1)
- Confidence tiers for data quality
- Checksum-based deduplication

### 4. Pipeline Layer

**Location:** `shared/axiom-esports-data/pipeline/`

**Architecture:**
- Central Job Coordinator (FastAPI-based)
- Async agent workers
- Redis for queue management (optional)
- GitHub Actions for scheduled execution

**Pipeline Stages:**
1. **Discover** - Find new matches/events
2. **Fetch** - Download raw data
3. **Verify** - Checksum and integrity
4. **Parse** - Extract structured data
5. **Transform** - Map to KCRITR schema
6. **Crossref** - Validate against external sources
7. **Store** - Write to PostgreSQL
8. **Index** - Update extraction_log

**Conflict Prevention:**
- Job deduplication (7-day window)
- Content drift detection
- Distributed locking
- Checksum comparison
- Rate limiting per source

**GitHub Actions Workflows:**
- `01-structure-check.yml` - Validate project structure
- `02-extraction-ci.yml` - Run extraction tests
- `03-validation-check.yml` - Data validation
- `05-daily-health-check.yml` - Daily health monitoring
- `06-weekly-analytics-refresh.yml` - Weekly analytics update
- `07-monthly-full-harvest.yml` - Monthly full data harvest

### 5. Simulation Layer

**Location:** `simulation-game/`

**Technology:**
- Godot 4.x Engine
- GDScript for game logic
- C# simulation core (`tactical-fps-sim-core-updated/`)

**Features:**
- 20 TPS (ticks per second) fixed timestep
- Deterministic with seeded RNG
- Raycast and TTK duel engines
- Economy system simulation
- Smoke field and utility mechanics

**Key Components:**
- `MatchEngine.gd` - Core match simulation
- `Agent.gd` - AI agent behavior
- `CombatResolver.gd` - Combat resolution
- `DuelResolver.gd` - Duel mechanics

**Export System:**
- `LiveSeasonModule.gd` - Match data export to API
- `ExportClient.gd` - HTTP client for API communication
- Enforces data partition firewall at export time

### 6. Analytics Layer

**Location:** `shared/axiom-esports-data/analytics/`

**Components:**
- **SimRating** - Player performance rating system
- **RAR** - Role-adjusted replacement value
- **Investment Grader** - Player investment grades (A+ to D)
- **Temporal Analysis** - Age curves, decay weights
- **Guardrails** - Leakage detection, overfitting prevention

**Key Metrics:**
- SimRating - Composite performance score
- RAR Score - Role-adjusted replacement value
- Investment Grade - A+, A, B, C, D
- Confidence Tier - Data quality indicator

## Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Godot     │────▶│  Pipeline   │────▶│  PostgreSQL │
│ Simulation  │     │  Extractor  │     │  Database   │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                      ┌────────▼────────┐
                                      │   Staging       │
                                      │   System        │
                                      └────────┬────────┘
                                               │
                                      ┌────────▼────────┐
                                      │   FastAPI       │
                                      │   Backend       │
                                      └────────┬────────┘
                                               │
                                      ┌────────▼────────┐
                                      │   React Web     │
                                      │   Frontend      │
                                      └─────────────────┘
```

## Security Architecture

### Data Partition Firewall

**Purpose:** Prevent game-internal data from reaching public web

**GAME_ONLY_FIELDS (Blocked):**
- `internalAgentState` - AI decision tree
- `radarData` - Real-time positions
- `detailedReplayFrameData` - Per-tick frames
- `simulationTick` - Engine counter
- `seedValue` - RNG seed
- `visionConeData` - Agent vision
- `smokeTickData` - Smoke state
- `recoilPattern` - Weapon recoil

**Enforcement Points:**
1. **Game Export** (`LiveSeasonModule.gd`) - Strips fields at source
2. **API Middleware** (`firewall.py`) - Validates API responses
3. **Staging System** (`WebExportForm`) - Firewall-verified flag
4. **Schema Validation** (`stats-schema`) - TypeScript type safety
5. **CI/CD Testing** - Automated firewall tests

### Staging System

**Location:** `shared/api/src/staging/`

**Components:**
- `ingest_service.py` - Central data intake
- `game_export_form.py` - Full data access for game
- `web_export_form.py` - Firewall-enforced for web
- `data_collection_service.py` - Pipeline orchestration

**Data Flow:**
1. Data enters via `StagingIngestService.ingest()`
2. SHA-256 checksum computed and validated
3. Firewall check for web-bound data
4. Exported to appropriate store (game or web)
5. Immutable audit trail in `staging_export_log`

## SATOR Square Visualization

**Location:** `shared/axiom-esports-data/visualization/sator-square/`

The SATOR Square is a 5-layer palindromic visualization system:

```
S A T O R
A R E P O
T E N E T
O P E R A
R O T A S
```

**Layer 1: SATOR** - Golden Halo System
- Marks high-impact player moments (Plant, MVP, Hotstreak, Ace)
- D3.js SVG rendering

**Layer 2: OPERA** - Fog of War
- Uncertainty visualization with animated fog
- WebGL Canvas with GLSL shaders

**Layer 3: TENET** - Area Control Grading
- Zone control visualization (A→D grades)
- Colored polygons per map zone

**Layer 4: AREPO** - Death Stains
- Death location persistence
- Multikill markers and clutch crowns

**Layer 5: ROTAS** - Rotation Trails
- Player movement trails
- WebGL with motion dust particles

## Deployment Architecture

### Zero-Cost Stack

| Component | Service | Free Tier | Cost |
|-----------|---------|-----------|------|
| Database | Supabase | 500MB, 2M reads | $0 |
| API | Render | 512MB, 750hrs | $0 |
| Web | Vercel | 100GB bandwidth | $0 |
| Static | GitHub Pages | 1GB, 100GB | $0 |
| CI/CD | GitHub Actions | 2000 mins | $0 |

### Cold Start Mitigation
- Keepalive cron (GitHub Actions)
- Health endpoint pinging
- Connection pooling (min=1, max=5)

### Environment Configuration

**API Environment Variables:**
```bash
DATABASE_URL=postgresql://user:pass@host:6543/db  # Supabase pooler
APP_ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://sator-web.vercel.app
```

**Web Environment Variables:**
```bash
VITE_API_URL=https://sator-api.onrender.com
```

## Monitoring & Observability

### Health Checks
- Database connectivity
- API response times
- Data freshness by source
- Pipeline queue depth
- Agent status

### Developer Dashboard
**Location:** `shared/axiom-esports-data/monitoring/dev_dashboard/`

- Port 8095 for local development
- Real-time pipeline metrics
- Agent health monitoring
- Alert management

### Pipeline Dashboard
**Location:** `shared/axiom-esports-data/pipeline/monitoring/`

- Queue depth visualization
- Job status tracking
- Rate limit monitoring
- Error reporting

### Alert Channels
- Slack webhooks
- Email notifications
- PagerDuty integration
- GitHub Issues for data discrepancies

## Development Workflow

### Local Development

```bash
# Start database
docker-compose -f shared/axiom-esports-data/infrastructure/docker-compose.yml up -d

# Run database setup
./shared/axiom-esports-data/infrastructure/setup.sh

# Start API
cd shared/axiom-esports-data/api
pip install -r requirements.txt
uvicorn main:app --reload

# Start Web
cd shared/apps/sator-web
npm install
npm run dev

# Run data collection
python -m api.src.staging.data_collection_service
```

### Testing

```bash
# Backend tests
pytest shared/axiom-esports-data/

# Frontend tests
npm run test --workspace=@sator/sator-web

# Firewall tests
npm run test:firewall

# Schema validation
npm run validate:schema
```

### Monorepo Scripts

```bash
# Root package.json scripts
npm run build          # Build all workspaces
npm run typecheck      # TypeScript check all
npm run test:firewall  # Test data partition firewall
npm run validate:schema # Validate stats schema
```

## Technology Decisions

### Why FastAPI?
- Async Python performance
- Automatic OpenAPI docs
- Pydantic validation
- Native asyncpg support

### Why PostgreSQL + TimescaleDB?
- Relational data integrity
- Time-series optimization
- Hypertables for performance
- JSONB flexibility

### Why React + Vite?
- Fast development HMR
- TypeScript support
- Small bundle size
- Modern tooling

### Why Godot?
- Open source
- Deterministic physics (20 TPS)
- GDScript flexibility
- Export to multiple platforms

### Why Monorepo Structure?
- Shared packages (stats-schema, data-partition-lib)
- Unified versioning
- Cross-project tooling
- Simplified CI/CD

## Performance Considerations

### Database
- Connection pooling (max 5 for free tier)
- Query result caching
- TimescaleDB chunking (90 days)
- Strategic indexes for common queries

### API
- Async endpoints
- Response caching headers
- Gzip compression
- Graceful error handling

### Web
- Code splitting via Vite
- TanStack Query caching
- Lazy loaded components
- Optimized bundle size

## Scalability Path

### Current: Free Tier
- Handles ~1000 concurrent users
- ~10k matches/day extraction
- 500MB database storage

### Growth: Paid Tier
- Supabase Pro ($25/mo) - 8GB, 100M reads
- Render Starter ($7/mo) - Always on
- Vercel Pro ($20/mo) - 1TB bandwidth

### Enterprise: Self-Hosted
- AWS RDS PostgreSQL
- Kubernetes cluster
- CDN for static assets
- Dedicated compute

## Troubleshooting

### Database Connection Issues
- Check DATABASE_URL format
- Verify Supabase connection pooler (port 6543)
- Check SSL mode settings
- Verify JIT is disabled (performance)

### API Cold Starts
- Verify keepalive workflow is running
- Check RENDER_API_URL secret
- Monitor Render dashboard
- Consider paid tier for production

### Pipeline Failures
- Check `extraction_jobs` table status
- Review agent heartbeats
- Verify rate limits not exceeded
- Check `extraction_conflicts` table

### Firewall Violations
- Run `npm run test:firewall`
- Check `LiveSeasonModule.gd` for proper sanitization
- Verify `FantasyDataFilter` is up to date
- Review staging export forms

## Project Structure

```
sator/
├── simulation-game/           # Godot 4 simulation
│   ├── scenes/               # Godot scenes
│   ├── scripts/              # GDScript files
│   ├── Defs/                 # Game definitions
│   └── tactical-fps-sim-core-updated/  # C# core
│
├── shared/
│   ├── apps/
│   │   ├── sator-web/        # React web platform
│   │   └── radiantx-game/    # Godot export modules
│   │
│   ├── packages/
│   │   ├── stats-schema/     # TypeScript types
│   │   └── data-partition-lib/  # Firewall library
│   │
│   ├── api/
│   │   └── src/staging/      # Staging system
│   │
│   ├── axiom-esports-data/   # Data pipeline & API
│   │   ├── api/              # FastAPI backend
│   │   ├── pipeline/         # ETL pipeline
│   │   ├── extraction/       # Data extractors
│   │   ├── analytics/        # Analytics engine
│   │   ├── infrastructure/   # DB migrations
│   │   └── monitoring/       # Observability
│   │
│   └── docs/                 # Documentation
│
├── website/                  # Static website
└── ARCHITECTURE.md          # This file
```

## References

- [Godot Documentation](https://docs.godotengine.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [React Documentation](https://react.dev/)

## Internal Documentation

- `shared/docs/FIREWALL_POLICY.md` - Data partition firewall
- `shared/docs/STAGING_SYSTEM.md` - Staging system
- `shared/axiom-esports-data/DUAL_GAME_ARCHITECTURE.md` - CS+Valorant pipeline
- `shared/axiom-esports-data/docs/SATOR_ARCHITECTURE.md` - Visualization layers
- `shared/axiom-esports-data/docs/DATA_DICTIONARY.md` - Field definitions
- `shared/axiom-esports-data/docs/API_REFERENCE.md` - API documentation
