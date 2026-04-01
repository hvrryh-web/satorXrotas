# SATOR Staging System Documentation

## Overview

The SATOR staging system is the central data layer connecting the two independent
projects in the monorepo:

1. **RadiantX (Game)** — Offline deterministic tactical FPS simulation
2. **SATOR Web** — Online public statistics platform

All data flows through the staging system before reaching project-specific stores.
This ensures data integrity, firewall compliance, and full auditability.

---

## Architecture

```
Data Sources → Staging Ingest Queue → Export Forms → Project Stores
                     ↑                      │
               Automated Collection         ├── Game Data Store (full access)
               (data_collection_service)    └── Web Data Store (firewall-verified)
```

### Components

| Component | File | Purpose |
|-----------|------|---------|
| **Ingest Service** | `api/src/staging/ingest_service.py` | Central data intake, validation, checksumming |
| **Game Export Form** | `api/src/staging/game_export_form.py` | Transforms staging → game format (full access) |
| **Web Export Form** | `api/src/staging/web_export_form.py` | Transforms staging → web format (firewall enforced) |
| **Data Collection** | `api/src/staging/data_collection_service.py` | Automated pipeline orchestration |
| **Safety Config** | `api/src/staging/staging_safety_protocol.json` | Protocol and safety rules |
| **DB Migration** | `axiom-esports-data/infrastructure/migrations/005_staging_system.sql` | Database schema |

---

## Database Schema

### Shared Tables

**`staging_ingest_queue`** — Central intake buffer for all incoming data.
- Receives data from game, analytics, scrapers, manual entry
- Validates, checksums, and queues for export
- Status flow: `pending` → `validated` → `exported` (or `rejected`)

**`staging_static_base`** — Versioned snapshots of static definitions.
- Agents, weapons, utilities, rulesets, maps, role baselines
- One active version per domain at any time
- Old versions are superseded but retained for history

**`staging_export_forms`** — Transform rules for each project.
- Game forms: full payload, no field stripping
- Web forms: firewall enforcement, field mapping to public schema

**`staging_export_log`** — Immutable audit trail of all exports.

**`staging_health_status`** — Pipeline health monitoring.

### Game Tables

**`game_data_store`** — Definitions, event logs, and replays for RadiantX.
- Types: `agent_def`, `weapon_def`, `utility_def`, `ruleset_def`, `map_def`, `event_log`, `match_replay`
- Full data access, no firewall filtering

### Web Tables

**`web_data_store`** — Sanitized public stats for SATOR Web.
- Types: `player_stats`, `match_summary`, `leaderboard`, `tournament_result`
- All records must have `firewall_verified = TRUE`
- GAME_ONLY_FIELDS are stripped at export time

---

## Data Flow

### 1. Collection → Staging

Data enters from multiple sources:
- **Game definitions:** Read from `Defs/` and `maps/` directories
- **Analytics scraping:** VLR.gg scrapers deposit match/player data
- **Analytics calculations:** SimRating, RAR, investment grades
- **Manual entry:** One-off corrections or additions

All data passes through `StagingIngestService.ingest()`:
1. SHA-256 checksum computed
2. Duplicate detection via checksum
3. Payload validated against schema
4. Firewall check for web-bound data
5. Queued with status `validated` or `rejected`

### 2. Staging → Game Store

`GameExportForm` pulls validated records and exports:
- Definitions → `game_data_store` as type-specific records
- Event logs → `game_data_store` with full event data
- Replays → `game_data_store` with complete replay payload
- **No firewall filtering** — game has full access to all data

### 3. Staging → Web Store

`WebExportForm` pulls validated records and exports with firewall:
1. `strip_game_only_fields()` — Recursively removes blacklisted fields
2. `map_to_public_schema()` — Maps KCRITR fields to public Statistics type
3. `verify_firewall_compliance()` — Final check before storage
4. Records stored with `firewall_verified = TRUE`

---

## Safety Protocols

### Data Integrity
- SHA-256 checksums on all payloads (mandatory)
- Duplicate detection prevents re-ingestion
- Raw extraction records are immutable (DB trigger enforced)

### Firewall Enforcement
- Web exports always strip GAME_ONLY_FIELDS
- Recursive field scanning catches nested violations
- Violations are blocked, logged, and alertable
- `firewall_verified` flag required on all web records

### Audit Trail
- All ingests logged with source, timestamp, agent name
- All exports logged with form, target, and record IDs
- All rejections logged with validation errors
- Health checks logged for pipeline monitoring

### Data Retention
- Staging queue: 90 days
- Export log: 365 days
- Health checks: 30 days
- Static base: 5 versions per domain
- Raw extractions: Immutable forever

---

## Usage

### Quick Start

```bash
# Run full data collection
cd /workspaces/RadiantX
python -m api.src.staging.data_collection_service

# Start database (if needed)
docker-compose -f axiom-esports-data/infrastructure/docker-compose.yml up -d
```

### Python API

```python
from api.src.staging import (
    StagingIngestService,
    GameExportForm,
    WebExportForm,
    DataCollectionService,
)

# Full pipeline
service = DataCollectionService()
result = service.collect_all()

# Manual ingest
ingest = StagingIngestService()
record = ingest.ingest(
    source_system="analytics",
    payload_type="player_stat",
    payload={"player_id": "abc-123", "match_id": "m001", "kills": 25},
    ingested_by="my_script",
    target_project="both",
)

# Game export
game = GameExportForm(ingest_service=ingest)
game.export_definitions("agents", definitions)

# Web export (firewall enforced)
web = WebExportForm(ingest_service=ingest)
web.export_player_stats(player_records)
```

---

## Extending the System

### Adding a New Data Source
1. Create a new source constant in `ingest_service.py`
2. Validate against the allowed sources in `staging_safety_protocol.json`
3. Add collection logic to `data_collection_service.py`
4. Add export form rules to `staging_export_forms` table

### Adding a New Export Form
1. Add a new form class following the pattern in `game_export_form.py` or `web_export_form.py`
2. Register the form in `staging_export_forms` DB table
3. Add transform rules and firewall fields (if web-bound)
4. Update `data_collection_service.py` to use the new form

### Adding New Firewall Fields
1. Add the field to `GAME_ONLY_FIELDS` in both:
   - `api/src/staging/web_export_form.py`
   - `packages/data-partition-lib/src/FantasyDataFilter.ts`
2. Add to `staging_safety_protocol.json`
3. Run firewall tests: `npm run test:firewall`
4. Update `docs/FIREWALL_POLICY.md`

