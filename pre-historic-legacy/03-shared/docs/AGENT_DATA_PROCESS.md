# SATOR Staging System — AI Agent Data Process Guide

## Purpose

This document is the **mandatory context** for any AI agent (Claude, Kimi, Copilot,
or any automated tooling) performing data operations in the SATOR monorepo.

**Read this file before touching any data pipeline, staging service, or export form.**

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                                  │
│  Game (Defs/, maps/)  │  Scrapers (VLR.gg)  │  Analytics Config │
└──────────┬────────────┴──────────┬───────────┴──────┬───────────┘
           │                       │                   │
           ▼                       ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│              STAGING INGEST QUEUE                                │
│  api/src/staging/ingest_service.py                              │
│  - Validates payloads against schema                            │
│  - Computes SHA-256 checksums                                   │
│  - Detects duplicates                                           │
│  - Checks firewall for web-bound data                           │
│  - Queues for export                                            │
└──────────┬──────────────────────────────────┬───────────────────┘
           │                                   │
           ▼                                   ▼
┌────────────────────────┐    ┌────────────────────────────────┐
│   GAME EXPORT FORM     │    │     WEB EXPORT FORM            │
│   game_export_form.py  │    │     web_export_form.py         │
│   - Full data access   │    │     - FIREWALL ENFORCED        │
│   - No field stripping │    │     - Strips GAME_ONLY_FIELDS  │
│   - JSON for Godot     │    │     - Maps to public schema    │
└──────────┬─────────────┘    └──────────┬─────────────────────┘
           │                              │
           ▼                              ▼
┌────────────────────────┐    ┌────────────────────────────────┐
│   GAME DATA STORE      │    │     WEB DATA STORE             │
│   game_data_store (DB) │    │     web_data_store (DB)        │
│   - agent_def          │    │     - player_stats             │
│   - weapon_def         │    │     - match_summary            │
│   - map_def            │    │     - leaderboard              │
│   - event_log          │    │     All firewall_verified=TRUE │
│   - match_replay       │    │                                │
└────────────────────────┘    └────────────────────────────────┘
```

---

## Data Process Obligations

### 1. BEFORE Any Data Operation

- [ ] Read this file (`AGENT_DATA_PROCESS.md`)
- [ ] Review `api/src/staging/staging_safety_protocol.json`
- [ ] Identify which project the data flows to (game, web, or both)
- [ ] If web-bound: review `docs/FIREWALL_POLICY.md`

### 2. Ingesting Data

**Always use the ingest service.** Never write directly to project stores.

```python
from api.src.staging.ingest_service import StagingIngestService

service = StagingIngestService()
record = service.ingest(
    source_system="game",         # or "analytics", "scraper", "manual"
    payload_type="game_definition", # or "player_stat", "match_event", "replay_log"
    payload={"id": "weapon.ak", "data_domain": "weapons", ...},
    ingested_by="agent_name",
    target_project="game",        # or "web", "both"
)
```

### 3. Exporting to Game

```python
from api.src.staging.game_export_form import GameExportForm

game = GameExportForm()
game.export_definitions(data_domain="agents", definitions=[...])
game.export_match_events(match_id="m001", events=[...])
```

### 4. Exporting to Web (FIREWALL REQUIRED)

```python
from api.src.staging.web_export_form import WebExportForm

web = WebExportForm()
web.export_player_stats(player_records=[...])  # Auto-strips game-only fields
web.export_match_summary(match_records=[...])
web.export_leaderboard(player_records=[...])
```

### 5. Running Full Collection

```bash
cd /workspaces/RadiantX
python -m api.src.staging.data_collection_service
```

Or programmatically:

```python
from api.src.staging.data_collection_service import DataCollectionService

service = DataCollectionService()
result = service.collect_all()
print(result)
```

---

## Critical Rules

### NEVER DO:
1. **Never bypass the ingest service** — all data must be checksummed and validated
2. **Never write game-only fields to web stores** — firewall violations are logged and blocked
3. **Never modify raw extraction records** — immutable by database trigger
4. **Never use future data in analytics** — temporal wall must be respected
5. **Never skip checksum verification** — SHA-256 is mandatory for all payloads
6. **Never delete staging records** — mark as exported or rejected, never delete

### ALWAYS DO:
1. **Always ingest through the staging service** — provides checksums, validation, logging
2. **Always verify firewall compliance** for web-bound data
3. **Always log your agent name** in the `ingested_by` field
4. **Always check for duplicates** before ingesting (automatic via checksum)
5. **Always run health checks** after bulk operations
6. **Always update the export log** for auditability

---

## Data Flow Routines

### Daily Routine
1. Health check: verify staging queue freshness and capacity
2. Check for new data from scrapers or manual entry
3. Process validated records through export forms
4. Verify firewall compliance on all web exports
5. Log summary to `staging_export_log`

### Weekly Routine
1. Full integrity scan of all stores (checksum verification)
2. Review and clear exported records from staging queue
3. Update static base if game definitions changed
4. Generate export report for audit

### On-Demand (Ping-Based)
1. Game service requests definitions → GameExportForm serves from game_data_store
2. Web service requests stats → WebExportForm serves from web_data_store (firewall-verified)
3. New scraper data arrives → Ingest, validate, queue for export

---

## File Reference

| File | Purpose |
|------|---------|
| `api/src/staging/__init__.py` | Package init, exports all services |
| `api/src/staging/ingest_service.py` | Central data intake and validation |
| `api/src/staging/game_export_form.py` | Game project data transformation |
| `api/src/staging/web_export_form.py` | Web project data transformation (firewall) |
| `api/src/staging/data_collection_service.py` | Automated pipeline orchestration |
| `api/src/staging/staging_safety_protocol.json` | Safety and protocol configuration |
| `axiom-esports-data/infrastructure/migrations/005_staging_system.sql` | DB schema |
| `docs/FIREWALL_POLICY.md` | Data partition firewall rules |
| `packages/data-partition-lib/src/FantasyDataFilter.ts` | TypeScript firewall enforcement |
| `packages/stats-schema/src/types/Statistics.ts` | Public stats type contract |

---

## Firewall Quick Reference

**These fields must NEVER appear in web-bound data:**

| Field | Why |
|-------|-----|
| `internalAgentState` | Simulation-internal AI state |
| `radarData` | Hidden game state |
| `detailedReplayFrameData` | Per-tick simulation frames |
| `simulationTick` | Internal tick counter |
| `seedValue` | RNG seed (would allow replay prediction) |
| `visionConeData` | Partial observability data |
| `smokeTickData` | Internal tactical state |
| `recoilPattern` | Weapon internals |

---

## Staging Database Tables

| Table | Purpose | Project |
|-------|---------|---------|
| `staging_ingest_queue` | Central intake buffer | Shared |
| `staging_static_base` | Versioned definition snapshots | Shared |
| `game_data_store` | Game definitions and replays | Game |
| `web_data_store` | Sanitized public stats | Web |
| `staging_export_forms` | Transformation rules | Shared |
| `staging_export_log` | Audit trail | Shared |
| `staging_health_status` | Pipeline health monitoring | Shared |

---

## Attention Items for AI Agents

1. **Firewall is non-negotiable.** If you touch web data, verify compliance.
2. **Checksums are non-negotiable.** All data must be hashed before storage.
3. **Audit logging is non-negotiable.** All operations must be traceable.
4. **The staging queue is the single entry point.** No shortcuts.
5. **Raw data is immutable.** The DB will reject UPDATE/DELETE on raw records.
6. **When in doubt, reject the data** — false negatives are safer than violations.

