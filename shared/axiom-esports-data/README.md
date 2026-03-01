# Axiom Esports Data Infrastructure

Tactical FPS analytics platform for professional Valorant esports.
88,560 validated player performance records spanning 2020–2026.

## Quick Start

### Prerequisites
- Docker + Docker Compose
- Python 3.11+
- Node.js 20+

### 1. Database Setup

```bash
cd infrastructure
docker-compose up -d
# Wait for health checks to pass, then apply migrations:
psql $DATABASE_URL -f migrations/001_initial_schema.sql
psql $DATABASE_URL -f migrations/002_sator_layers.sql
psql $DATABASE_URL -f migrations/003_dual_storage.sql
psql $DATABASE_URL -f migrations/004_extraction_log.sql
```

### 2. Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Extraction Pipeline

```bash
cd extraction
pip install -r requirements.txt
# Delta mode (recommended): only fetches new/changed matches
python src/scrapers/epoch_harvester.py --mode=delta
```

### 4. Analytics

```bash
cd analytics
# Run validation suite
pytest tests/ -v
```

### 5. Frontend

```bash
cd visualization
npm install
npm start
```

## Architecture

See [AXIOM.md](AXIOM.md) for the full AI agent operational guide.

```
axiom-esports-data/
├── infrastructure/    # Docker, PostgreSQL migrations
├── extraction/        # VLR.gg scraping pipeline (Python)
├── analytics/         # SimRating, RAR, overfitting guardrails (Python)
├── visualization/     # SATOR Square frontend (React/D3/WebGL)
├── api/               # FastAPI REST service
├── scripts/           # CLI operational tools
├── config/            # Static configuration
└── docs/              # Documentation
```

## CI Status

| Check | Workflow |
|-------|---------|
| Structure | `01-structure-check.yml` |
| Daily Extraction | `02-extraction-ci.yml` |
| Data Quality | `03-validation-check.yml` |
| Release | `04-release.yml` |

## Data Quality Targets

- HLTV correlation: **r > 0.85**
- Duplicate rate: **< 0.01%**
- Temporal wall: **no future data in training set**
- Adversarial AUC: **< 0.55** (no distribution shift)

## Documentation

| File | Purpose |
|------|---------|
| [AXIOM.md](AXIOM.md) | AI agent operational guide |
| [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) | 37-field KCRITR schema |
| [docs/CONFIDENCE_TIERS.md](docs/CONFIDENCE_TIERS.md) | Confidence tier definitions |
| [docs/SATOR_ARCHITECTURE.md](docs/SATOR_ARCHITECTURE.md) | 5-layer visualization spec |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | REST endpoint reference |
| [docs/TRAIN_TEST_PROTOCOL.md](docs/TRAIN_TEST_PROTOCOL.md) | Temporal split protocol |
| [docs/EXTRACTION_EPOCHS.md](docs/EXTRACTION_EPOCHS.md) | Epoch I/II/III coverage |

## License

[CC BY-NC 4.0](LICENSE) — Non-commercial use with attribution.
