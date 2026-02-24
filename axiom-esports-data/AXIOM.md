# AXIOM.md — AI Agent Operational Guide

## Project Overview

**Axiom Esports Data Infrastructure** is a tactical FPS analytics platform targeting
professional Valorant esports. It extracts, validates, stores, and visualizes match
performance data across 88,560 records spanning 2020-2026.

**Key characteristics:**
- 37-field KCRITR schema with dual raw/reconstructed storage
- PostgreSQL 15 + TimescaleDB for time-series analytics
- Python extraction pipeline (VLR.gg primary, Liquipedia validation)
- SATOR Square 5-layer visualization (D3.js + WebGL)
- React/TypeScript frontend
- Overfitting guardrails with temporal train/test wall

## Repository Structure

```
axiom-esports-data/
├── .github/            # CI/CD workflows + agent specs
├── infrastructure/     # Docker, migrations, seed data
├── extraction/         # Python VLR scraper pipeline
├── analytics/          # SimRating, RAR, investment grading
├── visualization/      # SATOR Square React/D3/WebGL frontend
├── api/                # FastAPI service layer
├── scripts/            # CLI operational tools
├── data/               # GITIGNORED — large parquet/CSV files
├── reference/          # Ground truth fixtures and baselines
├── config/             # Static configuration files
└── docs/               # Documentation
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Database | PostgreSQL 15 + TimescaleDB |
| Storage | Parquet (raw), PostgreSQL (analytics) |
| Extraction | Python 3.11+, asyncio, aiohttp |
| Analytics | Python: pandas, scikit-learn, numpy |
| Frontend | React 18, TypeScript, D3.js, WebGL/Three.js |
| API | FastAPI |
| CI | GitHub Actions |

## Architecture

### Data Pipeline

```
VLR.gg → vlr_resilient_client.py
  → epoch_harvester.py (Epoch I/II/III)
  → match_parser.py + economy_inference.py + role_classifier.py
  → integrity_checker.py (SHA-256)
  → raw_repository.py  (IMMUTABLE parquet)
  → extraction_bridge.py  (schema translation)
  → reconstruction_repo.py  (separated FK)
  → PostgreSQL/TimescaleDB
  → analytics/src/* (SimRating, RAR, investment grades)
  → api/src/routes/* (REST endpoints)
  → visualization/sator-square/* (SATOR Square)
```

### SATOR Square Visualization Layers

| Layer | Name | Tech | Function |
|-------|------|------|----------|
| 1 | SATOR | D3.js SVG | Golden halo, planter/MVP, hotstreak |
| 2 | OPERA | WebGL | Fog of war, audio ripples, uncertainty |
| 3 | TENET | D3.js SVG | Area control grading, exclusion zones |
| 4 | AREPO | D3.js SVG | Death stains, multikill persistence, clutch crowns |
| 5 | ROTAS | WebGL | Rotation trails, LR balance wheel, motion dust |

### Key Constants

| Constant | Value | Location |
|----------|-------|----------|
| Tick rate | 20 TPS | reference (from sim core) |
| Training records | 88,560 | unified master |
| Historic records | 135,720 | raw parquet |
| Min maps for training | 50 | config/overfitting_guardrails.json |
| Max maps ceiling | 200 | config/overfitting_guardrails.json |
| Train cutoff | 2024-01-01 | analytics/src/guardrails/temporal_wall.py |
| VLR rate limit | 2.0s | extraction/src/scrapers/vlr_resilient_client.py |
| Validation target | r > 0.85 | analytics/tests/ |

## Coding Conventions

### Naming

- **Variables/functions:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Schema classes:** `*Schema` suffix (static definitions)
- **Engine classes:** `*Engine` suffix (runtime computation)

### Determinism & Overfitting Rules (Critical)

1. **Temporal wall enforced** — training data must predate 2024-01-01
2. **No hardcoded player IDs** in test files — use statistical ranges
3. **No model files committed** — `.pkl`, `.joblib` are gitignored
4. **Stratified sampling** — min 50 maps, max 200 maps per player
5. **Inverse confidence weighting** — low-confidence records upsampled

### Dual-Storage Protocol

- Raw extractions: NEVER modified after capture (`separation_flag = 1`)
- Reconstructions: Stored separately with `partner_datapoint_ref` FK
- SHA-256 checksums verified before any analytics processing

## Testing

### Running Tests

```bash
# Extraction tests
cd extraction && pytest tests/ -v

# Analytics tests (includes guardrail validation)
cd analytics && pytest tests/ -v

# API tests
cd api && pytest tests/ -v

# Frontend tests
cd visualization && npm test
```

### Test Coverage Requirements

- `test_schema_validation.py` — 37-field KCRITR schema completeness
- `test_integrity_checker.py` — SHA-256 checksum round-trip
- `test_temporal_wall.py` — no future data in training set
- `test_overfitting_guard.py` — adversarial train/test detection
- `test_simrating.py` — range assertions (200 < acs < 400, NOT acs == 278)
- `SatorLayer.test.tsx` — golden halo render smoke test

## CI Pipeline

**Workflow execution order:**
1. `01-structure-check.yml` — validates repo structure (fast, always first)
2. `02-extraction-ci.yml` — daily VLR scrape (scheduled)
3. `03-validation-check.yml` — data quality gates on push/PR
4. `04-release.yml` — CSV export on version tag

## Environment Variables

```bash
# Copy .env.example → .env (NEVER COMMIT .env)
DATABASE_URL=postgresql://user:pass@localhost:5432/axiom_esports
VLR_RATE_LIMIT=2.0
HLTV_API_KEY=optional_for_validation
GRID_API_KEY=optional_partnership
GITHUB_TOKEN=for_actions
DATA_RETENTION_DAYS=730
```

## Common Tasks for AI Agents

### Adding a new data source

1. Create scraper in `extraction/src/scrapers/`
2. Add parser in `extraction/src/parsers/`
3. Extend `extraction_bridge.py` to map new schema to KCRITR fields
4. Add cross-reference validation in `validation_crossref.py`
5. Update `DATA_DICTIONARY.md`

### Adding a new analytics metric

1. Add calculator in appropriate `analytics/src/` subdirectory
2. Follow `*Schema` (static) / `*Engine` (runtime) naming split
3. Write range-based tests (no hardcoded player values)
4. Run overfitting guard against new metric

### Modifying SATOR Square layers

1. Edit the relevant `*Layer.tsx` in `visualization/sator-square/layers/`
2. GLSL shaders are in `visualization/sator-square/shaders/`
3. Spatial data hook: `hooks/useSpatialData.ts`
4. Run `SatorLayer.test.tsx` smoke test

### Running database migrations

```bash
cd infrastructure
docker-compose up -d
# Apply migrations in order:
psql $DATABASE_URL -f migrations/001_initial_schema.sql
psql $DATABASE_URL -f migrations/002_sator_layers.sql
psql $DATABASE_URL -f migrations/003_dual_storage.sql
psql $DATABASE_URL -f migrations/004_extraction_log.sql
```

## Documentation Index

| File | Purpose |
|------|---------|
| `docs/DATA_DICTIONARY.md` | 37-field KCRITR reference |
| `docs/CONFIDENCE_TIERS.md` | 100%→0% tier definitions |
| `docs/SATOR_ARCHITECTURE.md` | 5-layer visualization spec |
| `docs/API_REFERENCE.md` | REST endpoint documentation |
| `docs/TRAIN_TEST_PROTOCOL.md` | Temporal split protocol |
| `docs/EXTRACTION_EPOCHS.md` | Epoch I/II/III coverage |
