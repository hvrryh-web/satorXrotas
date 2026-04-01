# DATA_DICTIONARY.md — 37-Field KCRITR Schema Reference

## Overview

All player performance records in the Axiom system follow the **KCRITR Framework**
(Kills-Confidence-Role-Investment-Temporal-Reliability), a 37-field schema storing
both raw extracted data and computed analytics in one unified table.

## Field Reference

### Identity Fields (5)

| Field | Type | Description |
|-------|------|-------------|
| `player_id` | UUID | Stable player identifier across seasons |
| `name` | VARCHAR(100) | Player display name (may change — use player_id for joins) |
| `team` | VARCHAR(100) | Team name at time of match |
| `region` | VARCHAR(20) | Region: `Americas`, `Pacific`, `EMEA` |
| `role` | VARCHAR(30) | `Entry`, `IGL`, `Controller`, `Initiator`, `Sentinel` |

### Performance Fields (5)

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `kills` | SMALLINT | 0–100 | Total kills in map |
| `deaths` | SMALLINT | 0–100 | Total deaths in map |
| `acs` | NUMERIC(6,2) | 0–800 | Average Combat Score (raw, unmodified) |
| `adr` | NUMERIC(6,2) | 0–500 | Average Damage per Round |
| `kast_pct` | NUMERIC(5,2) | 0–100 | Kill/Assist/Survive/Trade percentage |

> ⚠️ **Never use raw `acs` in SimRating.** Use `adjusted_kill_value` (economy-normalized).

### RAR Metrics (4)

| Field | Type | Description |
|-------|------|-------------|
| `role_adjusted_value` | NUMERIC(8,4) | Performance vs. role baseline |
| `replacement_level` | NUMERIC(8,4) | Baseline for this role (see `config/role_matrix.json`) |
| `rar_score` | NUMERIC(8,4) | `role_adjusted_value / replacement_level` |
| `investment_grade` | CHAR(2) | `A+`, `A`, `B`, `C`, `D` |

### Extended Performance Fields (10)

| Field | Type | Description |
|-------|------|-------------|
| `headshot_pct` | NUMERIC(5,2) | Headshot percentage |
| `first_blood` | SMALLINT | First blood kills |
| `clutch_wins` | SMALLINT | 1vN clutch wins |
| `agent` | VARCHAR(50) | Agent played |
| `economy_rating` | NUMERIC(6,2) | Economy efficiency score |
| `adjusted_kill_value` | NUMERIC(8,4) | Economy-normalized kill value (use in SimRating) |
| `sim_rating` | NUMERIC(8,4) | Final SimRating score (z-score composite, ±5 range) |
| `age` | SMALLINT | Player age at match date |
| `peak_age_estimate` | SMALLINT | Estimated peak age for this role |
| `career_stage` | VARCHAR(20) | `rising`, `peak`, `declining` |

### Match Context Fields (5)

| Field | Type | Description |
|-------|------|-------------|
| `match_id` | VARCHAR(50) | VLR.gg match identifier |
| `map_name` | VARCHAR(50) | Map name (Ascent, Bind, Haven, etc.) |
| `tournament` | VARCHAR(100) | Tournament name |
| `patch_version` | VARCHAR(20) | Game patch at match time |
| `realworld_time` | TIMESTAMPTZ | Match timestamp (UTC, partitioned on this field) |

### Data Provenance Fields (8)

| Field | Type | Description |
|-------|------|-------------|
| `data_source` | VARCHAR(30) | `vlr_gg`, `liquipedia`, `hltv`, `grid` |
| `extraction_timestamp` | TIMESTAMPTZ | When record was extracted |
| `checksum_sha256` | CHAR(64) | SHA-256 of raw extraction payload |
| `confidence_tier` | NUMERIC(5,2) | 0–100 (see `CONFIDENCE_TIERS.md`) |
| `separation_flag` | SMALLINT | `0` = raw extraction, `1` = reconstructed |
| `partner_datapoint_ref` | UUID | FK to reconstructed record (if separation_flag=1) |
| `reconstruction_notes` | TEXT | Method and fields reconstructed |
| `record_id` | BIGSERIAL | Auto-increment row ID |

## Composite Primary Key

`(player_id, match_id, map_name)` — a player may appear once per map per match.

## Critical Constraints

1. `separation_flag = 0` records are **immutable** — database trigger prevents UPDATE/DELETE
2. `separation_flag = 1` records **must** have a `partner_datapoint_ref`
3. `acs` field stores raw VLR value — never modify it
4. `adjusted_kill_value` is always computed by `economy_inference.py`, never by scraper
5. `sim_rating` is always computed after training split — never pre-populated
