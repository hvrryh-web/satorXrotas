# SATOR Platform - Design Overview

## Executive Summary

The SATOR (RadiantX) platform is a three-part esports simulation and analytics ecosystem designed for professional Counter-Strike and Valorant esports. It combines deterministic game simulation, real-time data extraction, advanced statistical analytics, and a branded web interface.

**Design Philosophy:**
- **Porcelain³** - Branded aesthetic inspired by Ralph Lauren refinement, Apple minimalism, Nike energy, and 5 Gum mystique
- **Deterministic Simulation** - Reproducible 20 TPS game engine with seeded RNG
- **Zero-Cost Architecture** - Full production stack on free tiers
- **Data Security** - Multi-layer firewall preventing internal game data leakage

---

## System Design Principles

### 1. Separation of Concerns
```
┌─────────────────┐
│   Web Layer     │ React - User Interface
├─────────────────┤
│   API Layer     │ FastAPI - Business Logic
├─────────────────┤
│   Data Layer    │ PostgreSQL - Persistence
├─────────────────┤
│ Pipeline Layer  │ Python ETL - Data Collection
├─────────────────┤
│   Sim Layer     │ Godot 4 - Game Engine
└─────────────────┘
```

### 2. Dual-Game Architecture
- **Game Isolation**: CS and Valorant data never overlap
- **Partitioned Storage**: List partitioning by game type
- **Dedicated Extractors**: Source-specific scrapers (HLTV, VLR.gg)
- **Conflict Prevention**: Distributed locking and deduplication

### 3. Temporal Data Strategy
- **3 Epochs**: Historic (>2 years), Mature (3 months-2 years), Current (<3 months)
- **TimescaleDB**: Hypertables for time-series optimization
- **Compression**: Automatic after 30 days
- **Retention**: Configurable per epoch

### 4. Security-First Design
- **Data Partition Firewall**: 5 enforcement points
- **Least Privilege**: Role-based access control
- **Audit Logging**: All extractions tracked
- **Rate Limiting**: Per-source throttling

---

## Component Design

### Web Platform (React + TypeScript)

#### Porcelain³ Design System
**Color Philosophy:**
```
White Family:  Pristine → Cream → Ash → Cloud → Dirty
               (purity)      (warmth)    (industry)

Blue Family:   Porcelain → Abyssal → Navy → Royal → Ultramarine
               (calm)      (depth)   (trust) (luxury)

Gold Family:   Celestial → Metallic → Neon Yellows
               (divine)    (premium)  (energy)
```

**Quarterly Grid Pattern:**
- 4 resizable quadrants representing service areas
- Center HelpHub as focal point
- Click-to-expand interaction model
- Full-screen overlay for immersive experiences

**Animation Philosophy:**
- Framer Motion for physics-based animations
- Spring transitions for natural feel
- Staggered reveals for content hierarchy
- 3D perspective corridor for loading states

#### Component Architecture
```
App
├── Router
│   ├── LandingPage (SATOR³ branding)
│   ├── LoadingCorridor (3D animation)
│   ├── ServiceSelection (Quarter Grid)
│   │   ├── AdvancedAnalyticsHub
│   │   ├── StatsReferenceHub
│   │   ├── InfoHub
│   │   ├── GameHub
│   │   └── HelpHub (expandable)
│   └── DashboardPages
└── Providers (Query, Theme)
```

### API Layer (FastAPI)

#### Middleware Stack
```
Request → CORS → Rate Limit → Firewall → Router → Response
                ↓
         GAME_ONLY_FIELDS blocked
```

#### Endpoint Design
- RESTful API with OpenAPI documentation
- Async endpoints for I/O bound operations
- Health checks: /health, /ready, /live
- Prometheus metrics at /metrics

#### Database Integration
- asyncpg for async PostgreSQL
- Connection pooling (min: 2, max: 5)
- Automatic retry with exponential backoff
- Circuit breaker pattern for resilience

### Database Layer (PostgreSQL + TimescaleDB)

#### Schema Design
```
Entity Tables:     teams, players, tournaments

Match Tables:      matches (parent)
                   ├── matches_cs (partition)
                   └── matches_valorant (partition)

Performance:       player_performance (parent)
                   ├── player_performance_cs (partition)
                   └── player_performance_valorant (partition)

Pipeline:          extraction_jobs, extraction_log, raw_extractions
Monitoring:        health_checks, pipeline_alerts, maintenance_windows
```

#### Partitioning Strategy
- **List Partitioning**: By game type (cs/valorant)
- **Hypertables**: Time-series data with 7-day chunks
- **Compression**: 30-day automatic compression
- **Indexes**: B-tree on primary keys, BRIN on timestamps

### Data Pipeline (Python Async)

#### 8-Stage Pipeline
```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ Discover│ → │  Fetch  │ → │ Verify  │ → │  Parse  │
└─────────┘   └─────────┘   └─────────┘   └─────────┘
                                               ↓
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│  Index  │ ← │  Store  │ ← │ Crossref│ ← │Transform│
└─────────┘   └─────────┘   └─────────┘   └─────────┘
```

#### Queue Management
- **Priority Queues**: High/medium/low priority per game
- **Game Isolation**: Separate queues for CS/Valorant
- **Agent Management**: Worker lifecycle with heartbeat
- **Conflict Resolution**: Deduplication + content drift detection

#### Rate Limiting
- Per-source limits (HLTV: 1req/s, VLR: 2req/s)
- Token bucket algorithm
- Adaptive backoff on 429 responses
- Distributed rate limiting with Redis

### Simulation Layer (Godot 4)

#### Deterministic Design
- **Fixed Timestep**: 20 TPS physics
- **Seeded RNG**: Reproducible randomness
- **Snapshot System**: State serialization
- **Replay Capability**: Frame-perfect recreation

#### Data Export
- **LiveSeasonModule**: Match data extraction
- **ExportClient**: HTTP with retry logic
- **DataSanitizer**: GAME_ONLY_FIELDS filtering
- **Firewall Enforcement**: Pre-export validation

---

## Design Patterns

### 1. Repository Pattern
```python
# Abstract data access
class PlayerRepository:
    async def get_by_id(self, id: UUID) -> Player
    async def search(self, filters: Filters) -> List[Player]
```

### 2. Circuit Breaker
```python
# Fail fast on repeated failures
@circuit_breaker(threshold=5, timeout=60)
async def fetch_external_data():
    ...
```

### 3. Event Sourcing
```python
# Immutable event log
class ExtractionEvent:
    event_id: UUID
    timestamp: datetime
    source: str
    data_hash: str
    status: Status
```

### 4. Strategy Pattern
```python
# Pluggable extractors
class Extractor(ABC):
    @abstractmethod
    async def extract(self, match_id: str) -> Match
```

---

## Technology Stack Justification

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | React 18 + Vite | Fast HMR, small bundles, TypeScript native |
| **Styling** | Tailwind CSS | Utility-first, design system tokens |
| **Animation** | Framer Motion | Physics-based, React integration |
| **Backend** | FastAPI | Async Python, OpenAPI, Pydantic |
| **Database** | PostgreSQL + TimescaleDB | Relational + time-series optimization |
| **Pipeline** | Python asyncio | I/O bound, concurrent extraction |
| **Simulation** | Godot 4 | Open source, deterministic physics |
| **Deployment** | Vercel/Render/Supabase | Zero-cost, managed services |

---

## Performance Design

### Database
- Connection pooling (2-5 connections)
- Query result caching (Redis)
- TimescaleDB chunking (7-day intervals)
- Automatic compression after 30 days

### API
- Async endpoints for concurrency
- Response caching with ETags
- Gzip compression for >1KB responses
- Rate limiting to prevent abuse

### Web
- Code splitting by route
- Lazy loading for heavy components
- Image optimization (WebP, srcset)
- Service worker for offline caching

### Pipeline
- Async HTTP clients (aiohttp)
- Connection reuse with keep-alive
- Batch inserts (100 rows/batch)
- Parallel extraction workers

---

## Scalability Path

### Phase 1: Free Tier (Current)
- 500MB database (Supabase)
- 750hrs API runtime (Render)
- 100GB web bandwidth (Vercel)
- Handles ~1,000 concurrent users

### Phase 2: Growth ($72/month)
- Supabase Pro ($25) - 8GB storage
- Render Starter ($7) - Always on
- Vercel Pro ($20) - 1TB bandwidth
- Redis Cloud ($20) - Caching

### Phase 3: Scale ($500/month)
- AWS RDS PostgreSQL
- ECS/Fargate for API
- CloudFront CDN
- Dedicated Redis cluster

---

## Monitoring Design

### Health Check Layers
```
Layer 1: Infrastructure (Database, Redis)
Layer 2: API Services (FastAPI endpoints)
Layer 3: Data Pipeline (Extractors, Queue)
Layer 4: Web Platform (React, Vercel)
Layer 5: Simulation (Godot export)
Layer 6: Security (Firewall, Auth)
Layer 7: External (HLTV, VLR.gg)
```

### Alerting Strategy
- **Critical**: Page/SMS (database down)
- **Warning**: Slack/email (high latency)
- **Info**: Dashboard only (successful deploy)

### Metrics Collection
- Response times (p50, p95, p99)
- Error rates by endpoint
- Queue depth and processing time
- Data freshness by source

---

## Security Design

### Data Classification
| Level | Fields | Access |
|-------|--------|--------|
| **Public** | match_score, player_name | Web/API |
| **PROTECTED** | player_stats, team_metrics | API only |
| **GAME_ONLY** | internalAgentState, radarData | Game only |

### Firewall Enforcement Points
1. **Game Export**: LiveSeasonModule.gd filters fields
2. **API Middleware**: firewall.py validates requests
3. **Schema Validation**: TypeScript types enforce contracts
4. **Staging System**: WebExportForm enforces boundaries
5. **CI/CD Testing**: Automated firewall tests

### Authentication Strategy
- JWT tokens for API access
- Row-level security in PostgreSQL
- API key authentication for pipeline
- GitHub OAuth for admin dashboard

---

## SATOR Square Visualization

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

---

## Conclusion

The SATOR platform demonstrates a well-architected system with:
- Clear separation of concerns across 5 layers
- Security-first design with multi-layer firewall
- Zero-cost deployment without compromising functionality
- Scalable architecture with clear growth path
- Branded user experience with Porcelain³ design system

The design prioritizes reliability, security, and cost-efficiency while maintaining flexibility for future growth.
