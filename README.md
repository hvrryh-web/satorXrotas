# SATOR / RadiantX Platform

<p align="center">
  <img src="website/favicon.svg" alt="SATOR Logo" width="120">
</p>

<p align="center">
  <strong>Porcelain³ Intelligence Platform for Professional Esports</strong><br>
  Deterministic tactical FPS simulation • Advanced analytics • Real-time data
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#deployment">Deployment</a>
</p>

---

## Overview

SATOR (also known as **RadiantX**) is a comprehensive esports intelligence platform combining:

1. **RadiantX** — Deterministic tactical FPS simulation (Godot 4)
2. **Axiom Esports Data** — Python analytics pipeline with SATOR Square visualization
3. **SATOR Web** — Branded React platform with quarterly grid navigation

### Key Capabilities

- 🎮 **Match Simulation**: 20 TPS deterministic engine with seeded RNG
- 📊 **Advanced Analytics**: SimRating, RAR metrics, predictive models
- 🔍 **Dual-Game Support**: Counter-Strike + Valorant data collection
- 🎨 **Branded Interface**: Porcelain³ design system (RL × Apple × Nike × 5 Gum)
- 🔒 **Security**: Data partition firewall preventing internal data leakage
- 💰 **Zero-Cost Deployment**: Full stack on free tiers

## Features

### Web Platform
- **Landing Page**: Animated SATOR³ branded entry
- **Loading Corridor**: 3D perspective transition animation
- **Service Selection**: Quarterly grid with 5 hubs
  - AdvancedAnalyticsHub (Gold)
  - Stats*ReferenceHub (Neon Blue)
  - InfoHub (Pastel Blue)
  - GameHub (Navy Blue)
  - HelpHub (Center, expandable with health dashboard)
- **Responsive Design**: Mobile-first with glass morphism

### Data Pipeline
- **Dual Collection**: CS (HLTV) + Valorant (VLR.gg)
- **Conflict Prevention**: Deduplication, content drift detection
- **Real-time**: Async workers with job queue
- **Monitoring**: Health checks, alerting, dashboard

### Game Simulation
- **Deterministic**: Reproducible matches with seeded RNG
- **20 TPS**: Fixed timestep physics
- **Data Export**: Firewall-protected extraction

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  React Web (Vercel)     │  Porcelain³ Design System         │
│  FastAPI (Render)       │  Data Partition Firewall          │
│  PostgreSQL (Supabase)  │  TimescaleDB + Partitioning       │
│  Pipeline (GitHub)      │  CS + Valorant Extractors         │
│  Godot (Local)          │  Deterministic Simulation         │
└─────────────────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.

## Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- PostgreSQL 15 (or Docker)
- Godot 4.x (for simulation)

### 1. Clone & Setup
```bash
git clone https://github.com/username/satorx.git
cd satorx

# Install dependencies
npm install
cd shared/axiom-esports-data && pip install -r requirements-pipeline.txt
```

### 2. Database Setup
```bash
cd shared/axiom-esports-data/infrastructure
docker-compose up -d
# Run setup script (setup.sh for Linux/Mac, setup.ps1 for Windows)
```

### 3. Environment Configuration
```bash
# Copy example env files
cp shared/axiom-esports-data/.env.example shared/axiom-esports-data/.env

# Edit with your values
```

### 4. Start Development
```bash
# Terminal 1: API
cd shared/axiom-esports-data/api
uvicorn main:app --reload --port 8000

# Terminal 2: Web (Sator-Web)
cd shared/apps/sator-web
npm run dev

# Terminal 3: Pipeline (optional)
python -m pipeline.orchestrator run --mode=delta
```

### 5. Access Application
- Web: http://localhost:5173
- API Docs: http://localhost:8000/docs
- Pipeline Dashboard: http://localhost:8090

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture & design decisions |
| [CHANGELOG.md](CHANGELOG.md) | Version history & changes |
| [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md) | Free-tier deployment guide |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | Step-by-step deployment |
| [AGENTS.md](AGENTS.md) | AI agent working guide |
| [DUAL_GAME_ARCHITECTURE.md](shared/axiom-esports-data/DUAL_GAME_ARCHITECTURE.md) | CS + Valorant collection |

### Component Documentation
- `shared/axiom-esports-data/pipeline/` - Pipeline source
- `shared/axiom-esports-data/api/` - FastAPI backend
- `shared/apps/sator-web/` - React web platform
- `shared/axiom-esports-data/monitoring/` - Dashboard source
- `website/` - Static marketing site with Porcelain³ design system

## Deployment

### Zero-Cost Stack
All services run on free tiers:

| Service | Provider | Free Tier |
|---------|----------|-----------|
| Database | Supabase | 500MB |
| API | Render | 750hrs/mo |
| Web | Vercel | 100GB/mo |
| Static | GitHub Pages | 1GB |

### Deploy in 5 Minutes
```bash
# 1. Deploy Database (Supabase)
# Create project at https://app.supabase.com
# Run migrations: psql $DB_URL -f migrations/*.sql

# 2. Deploy API (Render)
git push origin main  # Auto-deploys via render.yaml

# 3. Deploy Web (Vercel)
cd shared/apps/sator-web
vercel --prod
```

See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for detailed instructions.

## Project Structure

```
satorx/
├── website/                    # Static marketing site
│   ├── design-system/         # Porcelain³ design system
│   ├── src/                   # Source assets
│   └── ...
├── simulation-game/           # Godot 4 project (RadiantX)
│   ├── scripts/               # GDScript logic
│   ├── scenes/                # Game scenes
│   ├── maps/                  # Map definitions
│   └── ...
├── shared/
│   ├── apps/
│   │   ├── sator-web/        # React web platform
│   │   └── radiantx-game/    # Godot modules
│   ├── axiom-esports-data/   # Python pipeline
│   │   ├── api/              # FastAPI backend
│   │   ├── pipeline/         # ETL orchestration
│   │   ├── extraction/       # Web scrapers (HLTV, VLR.gg)
│   │   ├── analytics/        # Statistical models
│   │   ├── monitoring/       # Dev dashboard
│   │   ├── infrastructure/   # Docker, migrations
│   │   └── visualization/    # SATOR Square viz
│   ├── api/                  # Shared API utilities
│   └── packages/             # TypeScript shared
│       ├── stats-schema/     # Public types
│       ├── data-partition-lib/ # Firewall library
│       └── api-client/       # API client library
└── .github/workflows/        # CI/CD
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Framer Motion |
| **Backend** | FastAPI, Python 3.11, asyncpg, Pydantic |
| **Database** | PostgreSQL 15, TimescaleDB |
| **Pipeline** | Python, asyncio, aiohttp, BeautifulSoup |
| **Simulation** | Godot 4, GDScript |
| **DevOps** | Docker, GitHub Actions, Vercel, Render |

## Skills System

This project includes a comprehensive skill system for AI agents:

```
C:\Users\<user>\.agents\skills\
├── sator-project/            # Multi-component orchestration
├── sator-frontend/           # React development
├── sator-fastapi/            # Python API development
├── sator-database/           # PostgreSQL/TimescaleDB
├── sator-deployment/         # DevOps & deployment
├── sator-data-firewall/      # Security & data partition
├── axiom-data-pipeline/      # ETL pipeline
├── godot-simulation/         # Godot development
└── Expert Suite/             # General web development
    ├── frontend-architecture/
    ├── ui-ux-design/
    ├── web-performance/
    ├── web-accessibility/
    ├── modern-css/
    ├── advanced-typescript/
    ├── design-systems/
    └── web-animation/
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow
1. Create feature branch
2. Make changes
3. Run tests
4. Submit PR
5. Automated CI/CD deploys

## License

- **RadiantX Game**: MIT License
- **Axiom Esports Data**: CC BY-NC 4.0 (Non-commercial)
- **SATOR Web**: MIT License

## Acknowledgments

Design inspired by:
- **Ralph Lauren** - Classic refinement
- **Apple** - Clean minimalism
- **Nike** - Dynamic energy
- **5 Gum** - Dark mystique

---

<p align="center">
  <strong>◈ SATOR³ ◈</strong><br>
  <em>Porcelain Intelligence Platform</em>
</p>
