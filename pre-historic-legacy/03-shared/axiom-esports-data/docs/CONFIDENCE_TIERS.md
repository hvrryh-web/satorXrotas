# CONFIDENCE_TIERS.md — Data Confidence Tier Definitions

## Overview

Every record in the Axiom system carries a `confidence_tier` score (0–100)
indicating the reliability of the data provenance.

## Tier Definitions

### Tier 100 — Direct Extraction, Verified
- **Criteria:** Directly scraped from VLR.gg AND cross-verified against ≥2 external sources
- **Training weight:** 1.0 (full weight)
- **Example:** VCT Champions match, confirmed by Liquipedia and GRID

### Tier 75 — Single Source, Verified
- **Criteria:** Directly scraped from VLR.gg, not cross-verified
- **Training weight:** 0.75
- **Example:** Regional Challengers match with clean scorecard

### Tier 50 — Partially Reconstructed
- **Criteria:** Some fields inferred via ACS differential model or role inference
- **Training weight:** 0.50
- **Example:** Match where map-level stats were missing; round aggregates used

### Tier 25 — Primarily Reconstructed
- **Criteria:** Majority of fields are inferred; no external validation
- **Training weight:** 0.25
- **Example:** Early 2021 match with only team-level stats available

### Tier 0 — Unknown / Excluded
- **Criteria:** Provenance cannot be established
- **Training weight:** 0.0 — **excluded from all training**
- **Example:** Data imported from unverified third-party source

## Implementation

```python
# In analytics/src/guardrails/confidence_sampler.py
weights = 1.0 / df['confidence_tier'].clip(lower=1.0)
# Records with confidence=0 are excluded before sampling
```

## Relationship to Dual-Storage Protocol

- Tier 100/75: typically `separation_flag = 0` (raw extractions)
- Tier 50/25: typically `separation_flag = 1` (reconstructed records)
- Tier 0: excluded from `player_performance` entirely; stored only in `raw_extractions`
