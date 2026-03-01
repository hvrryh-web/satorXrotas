# EXTRACTION_EPOCHS.md — Epoch I/II/III Coverage

## Temporal Coverage

Total: 2020-12-03 to 2026-02-23 (1,908 days)

| Epoch | Date Range | Records | Confidence Floor | Notes |
|-------|-----------|---------|-----------------|-------|
| I | 2020-12-03 → 2022-12-31 | ~47,160 | 50% | Early era, partial coverage |
| II | 2023-01-01 → 2025-12-31 | ~135,720 | 75% | Primary training epoch |
| III | 2026-01-01 → present | Growing | 100% | Current season, delta only |

**Unified Master (validated):** 88,560 records
**Historic Archive (raw):** 135,720 records
**Total Extracted:** ~135,720 parquet records

## Epoch Harvester Architecture

```
EpochHarvester(mode='delta')
├── Epoch I Worker   — async, 2s rate limit
├── Epoch II Worker  — async, 2s rate limit
└── Epoch III Worker — async, 2s rate limit (incremental only)
     └── Semaphore(3) — max 3 concurrent requests
```

## Delta vs. Full Mode

- **Delta mode (default):** Queries `extraction_log` for records not yet extracted
  or where `last_modified_hash` has changed. ~90% reduction in VLR requests.
- **Full mode:** Re-scrapes entire epoch date range. Used only for schema migration
  or corruption recovery.

## Confidence Scoring by Epoch

Records receive confidence penalties for:
- Epoch I data (50% floor) — early VLR coverage gaps
- Single-map match scorecards (no round-level data)
- Missing economy fields (pre-economy patch matches)
- No cross-reference available for validation

## VLR.gg Rate Limiting

- Base delay: 2.0 seconds between requests
- Circuit breaker: 5 failures → 5 minute pause
- Retry backoff: 2s → 4s → 8s → 16s
- User agent rotation: 2 ethical bots declared
- Schema drift alert: Admin notified, fallback to cache
