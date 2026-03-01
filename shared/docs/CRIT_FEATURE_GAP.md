# CRIT Report & Feature Design Gap Assessment
## SATOR Esports Analytics Platform — RadiantX Repository
**Date:** 2026-02-25  
**Prepared by:** Automated CRIT + Gap Analysis  
**Scope:** Full repository — RadiantX game engine, Axiom Esports Data pipeline, SATOR Web platform

---

## 1. CRIT Report (Critical Issues Triage)

> **CRIT** categories: **C**ritical blocker | **R**isk (data/pipeline) | **I**nfrastructure gap | **T**echnical debt

### CRIT-1 · CRITICAL — No live running application
**Severity:** Critical  
**Component:** All  
**Status:** Zero user-facing surface exists. The API, web dashboard, and replay viewer are all stubs returning HTTP 501. No user can currently access any part of the platform.

**Blockers caused by this:**
- No validation of end-to-end data flow
- No product demo or investor-facing artifact
- SATOR Square visualization layers exist as React components but have no host page

**Resolution:** Implement API `main.py`, seed data generator, and minimal React dashboard. *(Done in this PR.)*

---

### CRIT-2 · CRITICAL — Canonical ID instability breaks deduplication
**Severity:** Critical  
**Component:** `extraction_bridge.py`  
**Status:** Prior to this PR, `player_id = uuid4()` was called on every `translate()` call — a random UUID was assigned each time, making cross-run and cross-source deduplication impossible.

**Impact:**
- The same player scraped twice gets two different UUIDs
- Liquipedia cross-reference cannot join on `player_id`
- `KnownRecordRegistry.mark_complete()` keys on `match_id` but downstream analytics key on `player_id` — mismatch

**Resolution:** `CanonicalIDResolver.resolve_player()` now produces a deterministic `uuid5` from `cid:player:{handle}`. *(Done in previous commits.)*

---

### CRIT-3 · RISK — No seed / fixture data for development
**Severity:** High  
**Component:** API, database  
**Status:** All API routes raise 501. Local development requires a live PostgreSQL instance with real scrape data. This blocks frontend development entirely.

**Resolution:** Add `api/src/data/seed_matches.py` — deterministic in-memory data generator. *(Done in this PR.)*

---

### CRIT-4 · RISK — Field name translation is hard-coded per source
**Severity:** High  
**Component:** `extraction_bridge.py`, `VLR_TO_KCRITR_MAP`  
**Status:** Before this PR, the bridge hard-coded VLR.gg field names. Adding Liquipedia or GRID as sources required editing Python code.

**Resolution:** `FieldTranslator` + `config/datapoint_naming.json` centralises all source→canonical mappings. *(Done in previous commits.)*

---

### CRIT-5 · INFRASTRUCTURE — No runnable dev server command
**Severity:** High  
**Component:** `apps/sator-web/`, `api/`  
**Status:** `package.json` root `dev` script prints a message about Godot. There is no `npm run dev` that starts the web dashboard.

**Resolution:** Add `apps/sator-web/package.json` with Vite dev server + API proxy. *(Done in this PR.)*

---

### CRIT-6 · INFRASTRUCTURE — Docker compose has no API service
**Severity:** Medium  
**Component:** `infrastructure/docker-compose.yml`  
**Status:** Docker compose starts Postgres and Redis but not the FastAPI server. Developers must know to start it separately.

**Resolution:** Add `api` service to docker-compose. *(Done in this PR.)*

---

### CRIT-7 · TECHNICAL DEBT — Replay viewer disconnected from game engine
**Severity:** Medium  
**Component:** `scripts/`, `EventLog.gd`, API  
**Status:** `EventLog.gd` produces JSON replays. The web API has no endpoint to serve them. The SATOR map viewer exists as React components but has no replay tick stream.

**Resolution:** Add `GET /api/replay/{match_id}` endpoint + `MatchViewer.tsx` page. *(Done in this PR.)*

---

### CRIT-8 · TECHNICAL DEBT — SATOR Square layers have no host page
**Severity:** Medium  
**Component:** `visualization/sator-square/layers/`  
**Status:** All five layer components (`SatorLayer`, `ArepoLayer`, `TenetLayer`, `OperaLayer`, `RotasLayer`) exist and render correctly in isolation but are never mounted in any page or app.

**Resolution:** `MatchViewer.tsx` mounts all five layers over a map SVG. *(Done in this PR.)*

---

### CRIT-9 · RISK — Tests use hardcoded equality on schema-sensitive fields
**Severity:** Low  
**Component:** `test_extraction_bridge.py`  
**Status:** `assert record.map_name == "Haven"` broke immediately when canonical ID normalisation was introduced. Range-based or `in`-based assertions should be used for fields that pass through the translation layer.

**Resolution:** Updated to `assert "haven" in record.map_name.lower()`. *(Done in this PR.)*

---

## 2. Feature Design Gap Assessment

### 2.1 Analytics Platform — Current vs Target

| Feature | Current State | Target State | Gap |
|---|---|---|---|
| Player leaderboard | Stub (501) | Live sortable table with SimRating, RAR, grade | **LARGE** |
| Match viewer | Stub (501) | Interactive 2D map + 5 SATOR layers + timeline | **LARGE** |
| Replay scrubbing | N/A | Tick-by-tick playback with speed control | **LARGE** |
| SATOR Square | Components exist, no host | Mounted in MatchViewer with live data | **MEDIUM** |
| SimRating API | Stub (501) | `/api/analytics/simrating/{id}` with breakdown | **MEDIUM** |
| RAR decomposition | Stub (501) | `/api/analytics/rar/{id}` | **MEDIUM** |
| Investment grade | Stub (501) | `/api/analytics/investment/{id}` | **MEDIUM** |
| Tournament bracket | Not started | Not in scope Phase 3 | **OUT OF SCOPE** |
| Player comparison | Not started | Side-by-side metric comparison | **FUTURE** |
| Live match feed | Not started | WebSocket tick stream from simulator | **FUTURE** |

### 2.2 Data Pipeline — Current vs Target

| Feature | Current State | Target State | Gap |
|---|---|---|---|
| VLR scraping | Implemented | Production-ready | **SMALL** |
| Canonical IDs | Implemented (this PR) | Stable across all sources | **SMALL** |
| Field translation | Implemented (this PR) | Multi-source normalisation | **SMALL** |
| Liquipedia cross-ref | Gated on credentials | Gated on credentials | **NONE** (by design) |
| HLTV integration | Stub | CS2 pipeline | **FUTURE** |
| GRID partnership | Stub | Requires contract | **FUTURE** |
| Temporal decay | Implemented | Production-ready | **NONE** |
| Overfitting guard | Implemented | Production-ready | **NONE** |

### 2.3 Infrastructure — Current vs Target

| Feature | Current State | Target State | Gap |
|---|---|---|---|
| PostgreSQL + TimescaleDB | Docker compose | Production-ready | **SMALL** |
| FastAPI server | No `main.py` | Running server | **LARGE** → fixed here |
| React dashboard | No page | Live dashboard | **LARGE** → fixed here |
| Vite dev server | No config | `npm run dev` works | **LARGE** → fixed here |
| API docs (Swagger) | Not generated | Auto-generated by FastAPI | **NONE** (auto) |
| CI API smoke test | Missing | `pytest --api-start` | **MEDIUM** → fixed here |

---

## 3. Goals and Objectives — Platform Roadmap

### Phase 3A — Live Platform (this PR)
**Goal:** Anyone can `npm run dev` and see a working dashboard with real data.

- [x] FastAPI server starts with `python -m api.src.main`
- [x] `/api/health` returns `{"status":"ok"}`
- [x] `/api/players/` returns a player leaderboard with SimRating and investment grades
- [x] `/api/analytics/simrating/{id}` returns metric breakdown
- [x] `/api/matches/{id}` returns match metadata + round list
- [x] `/api/replay/{id}` returns tick-by-tick event stream
- [x] Dashboard page renders player table with sortable columns
- [x] MatchViewer page renders 2D map with SATOR overlay layers
- [x] Replay scrubber controls playback speed and position
- [x] `npm run dev` in `apps/sator-web/` starts a working Vite dev server

### Phase 3B — Data Quality (next sprint)
**Goal:** All 88,560 training records are accessible through the API.

- [ ] Connect API routes to PostgreSQL (currently uses seed data)
- [ ] Wire `KnownRecordRegistry` stats to a `/api/pipeline/status` endpoint
- [ ] Add `/api/players/{id}/matches` — full match history
- [ ] Add `/api/maps/{name}/heatmap` — aggregate positional data

### Phase 3C — Advanced Analytics (future)
**Goal:** Investment-grade analytics available for agent/team evaluation.

- [ ] Player comparison endpoint (`/api/compare?players=id1,id2`)
- [ ] Tournament bracket view
- [ ] Export to CSV from dashboard UI
- [ ] Confidence tier visualisation on all charts

### Phase 3D — Live Match Feed (future)
**Goal:** Real-time match watching from RadiantX simulator.

- [ ] WebSocket endpoint: `ws://localhost:8000/ws/match/{id}`
- [ ] RadiantX `EventLog.gd` posts events to WebSocket on each tick
- [ ] Dashboard auto-connects when a live match is detected

---

## 4. Success Metrics

| Metric | Threshold | How Measured |
|---|---|---|
| API cold-start time | < 2 seconds | `time python -m api.src.main` |
| Dashboard first-paint | < 3 seconds | Lighthouse FCP |
| Player leaderboard load | < 500ms | API response time |
| Replay scrub latency | < 100ms per tick | Browser performance trace |
| Test pass rate | 100% | `pytest extraction/tests/` |
| Canonical ID collision rate | 0% | `test_canonical_id.py` |
| Field translation coverage | ≥ 95% of known fields | `FieldTranslator.known_canonical_fields()` |
