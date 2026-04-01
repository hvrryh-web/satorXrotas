# Agent Runbook — Extraction Pipeline Security Check
## SATOR Esports Analytics Platform — RadiantX Repository
**Version:** 1.0.0  
**Audience:** Future AI agents and data engineers onboarding to this pipeline  
**Purpose:** Step-by-step guide for reproducing the example scrape, running the security check, and interpreting results

---

## Overview

This runbook defines the **mandatory correctness verification workflow** every new pipeline agent or engineer must complete before being authorised to write live records to the database.

The workflow uses a **committed example fixture** (`extraction/fixtures/example_match.json`) as a known-good reference. You parse it, translate it, compare the output against the expected values, and discard the results. You do **not** store the example records — they are proof of correctness only.

### Key Terms

| Term | Definition |
|---|---|
| **Example record** | A `KCRITRRecord` with `separation_flag=9` and `match_id` starting with `EXAMPLE_`. Permanently isolated from live pipeline. |
| **Security check** | Comparison of a freshly-reproduced parse against the committed fixture. Required before any live scraping. |
| **Fixture** | `extraction/fixtures/example_match.json` — committed, immutable, version-controlled baseline. |
| **Corpus** | `ExampleCorpus` — the class that loads the fixture, runs the security check, and provides the `is_example()` guard. |
| **Live record** | Any `KCRITRRecord` with `separation_flag=0` (raw) or `separation_flag=1` (reconstructed). These enter the database. Example records never do. |

---

## Isolation Guarantees (What Protects the Live Database)

The following automatic safeguards prevent example records from contaminating live data:

1. **`ExampleCorpus.is_example(match_id)`** — returns `True` for any match_id starting with `EXAMPLE_`. Called by `KnownRecordRegistry.should_skip()` before every fetch.

2. **`ExtractionBridge.transform()`** — auto-stamps `separation_flag=9` when the match_id starts with `EXAMPLE_`. Live records always have flag 0 or 1.

3. **`KnownRecordRegistry.should_skip()`** — returns `True` immediately for any `EXAMPLE_*` match_id, bypassing all network I/O. Example records are never re-scraped.

4. **`harvest_protocol.json` → `exclusion_reasons.EXAMPLE_DATA`** — the reason code used when registering example IDs. Any record with this reason code is permanently excluded from analytics jobs.

5. **`separation_flag=9` analytics filter** — all analytics modules (SimRating, RAR, investment grader) must filter `WHERE separation_flag < 9` before computing metrics.

---

## The Security Check — Step by Step

### Prerequisites

```bash
cd axiom-esports-data
pip install -r extraction/requirements.txt
# Verify the fixture exists
ls extraction/fixtures/example_match.json
```

### Step 1 — Load the fixture

```python
from extraction.src.storage.example_corpus import ExampleCorpus

corpus = ExampleCorpus()
fixture = corpus.load_fixture()

print(f"Fixture version: {fixture['fixture_version']}")
print(f"Created by:      {fixture['created_by']}")
print(f"Expected players: {fixture['expected_parse']['player_count']}")
```

Expected output:
```
Fixture version: 1.0.0
Created by:      agent:pipeline-bootstrap
Expected players: 10
```

### Step 2 — Get the example HTML

```python
html, match_id = corpus.get_example_html()
print(f"Match ID: {match_id}")   # → EXAMPLE_000001
print(f"HTML length: {len(html)} chars")
```

### Step 3 — Parse the HTML

```python
from extraction.src.parsers.match_parser import MatchParser

parser = MatchParser()
raw = parser.parse(html, match_id)

# Verify basic structure
assert raw is not None, "Parser returned None — schema validation failed"
assert raw.vlr_match_id == "EXAMPLE_000001"
assert raw.map_name is not None
assert len(raw.players) == 10, f"Expected 10 players, got {len(raw.players)}"

print(f"✓ Parsed: {len(raw.players)} players, map={raw.map_name}, "
      f"tournament={raw.tournament}, patch={raw.patch_version}")
```

Expected output:
```
✓ Parsed: 10 players, map=Haven, tournament=VCT 2025 Example Event, patch=8.11
```

### Step 4 — Translate to KCRITR records

```python
from extraction.src.bridge.extraction_bridge import ExtractionBridge

bridge = ExtractionBridge()
records = bridge.transform(raw)

# Verify isolation flags
assert len(records) == 10
for record in records:
    assert record.separation_flag == 9, \
        f"Expected separation_flag=9, got {record.separation_flag} for {record.name}"
    assert record.match_id.startswith("EXAMPLE_"), \
        f"match_id does not have EXAMPLE_ prefix: {record.match_id}"

print(f"✓ {len(records)} records produced, all separation_flag=9")
```

### Step 5 — Run the security check

```python
result = corpus.security_check(raw, records)

print(result.summary())

if not result.passed:
    print("\nFailures:")
    for f in result.failures:
        print(f"  ✗ {f}")
    raise RuntimeError("Security check FAILED — do not proceed with live scraping")

print("\n✓ Security check PASSED — pipeline is verified")
print("  IMPORTANT: Discard these records. Do not store them in the live DB.")
```

### Step 6 — Discard the example records

```python
# This is intentional — the records are proof of correctness, not data imports.
del records
print("✓ Example records discarded")
```

### Full Script (copy-paste ready)

```python
#!/usr/bin/env python
"""
agent_security_check.py — Run the pipeline security check.

Usage:
    cd axiom-esports-data
    python scripts/agent_security_check.py

Exit code 0 = PASSED, 1 = FAILED
"""
import sys
import logging
logging.basicConfig(level=logging.INFO)

from extraction.src.storage.example_corpus import ExampleCorpus
from extraction.src.parsers.match_parser import MatchParser
from extraction.src.bridge.extraction_bridge import ExtractionBridge

def main() -> int:
    corpus = ExampleCorpus()

    # 1. Load fixture
    fixture = corpus.load_fixture()
    print(f"Fixture v{fixture['fixture_version']}")

    # 2. Get HTML
    html, match_id = corpus.get_example_html()

    # 3. Parse
    raw = MatchParser().parse(html, match_id)
    assert raw is not None, "Parser returned None"

    # 4. Translate
    records = ExtractionBridge().transform(raw)

    # 5. Security check
    result = corpus.security_check(raw, records)
    print(result.summary())

    if not result.passed:
        for f in result.failures:
            print(f"  ✗ {f}", file=sys.stderr)
        return 1

    # 6. Discard — do NOT store in live DB
    del records
    print("✓ Records discarded")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

---

## Interpreting Results

### PASSED

All of the following hold:
- 10 player records produced
- All `separation_flag == 9`
- All spot-checked players are within ±5% of expected numeric ranges
- All agent/map string fields match expected values (case-insensitive)

**→ You are clear to proceed with live scraping.**

### FAILED — `player_count`

```
player_count: expected 10, got 7
```

The parser did not find all player rows. Possible causes:
- `MatchParser._extract_players()` has a regression
- The fixture HTML has been modified (check `git diff`)

**→ Fix the parser. Do not proceed.**

### FAILED — `separation_flag`

```
separation_flag: 3 record(s) do not have flag=9
```

`ExtractionBridge.transform()` is not detecting the `EXAMPLE_` prefix.

**→ Check `ExtractionBridge.transform()` — the `ExampleCorpus.is_example()` call must be present.**

### FAILED — numeric field out of range

```
Player 'alpha' — acs=180.0 outside [209.0, 283.5] (expected range [220.0, 270.0] ± 5%)
```

The bridge is either losing the ACS value or the field translation is incorrect.

**→ Check `FieldTranslator` mapping for `acs` and `ExtractionBridge._safe_float()`.**

### FAILED — agent mismatch

```
Player 'alpha' — agent: expected 'jett' in 'cid:agent:reyna'
```

The agent canonical URI is wrong — the parser extracted the wrong agent.

**→ Check `MatchParser._extract_players()` image alt-text extraction.**

---

## Updating the Fixture

**Only update the fixture if the pipeline has intentionally changed in a way that invalidates the current expected values.** 

Steps:
1. Bump `fixture_version` in `example_match.json`
2. Update `expected_records` with new range bounds
3. Add a `_change_log` entry to the fixture explaining why it changed
4. Run `test_example_corpus.py` to confirm the new fixture passes
5. Commit the updated fixture file

Do NOT update the fixture to make a failing security check pass — fix the pipeline instead.

---

## Marking a New Example Record

If you need to add a second example fixture (e.g., for a different map or agent set):

1. Create a new file `extraction/fixtures/example_{name}.json` following the same schema
2. Use a unique match_id with the `EXAMPLE_` prefix (e.g., `EXAMPLE_000002`)
3. Set `separation_flag: 9` in `expected_records`
4. Add the fixture path to `harvest_protocol.json` → `example_corpus.additional_fixtures`
5. Add a corresponding test in `test_example_corpus.py`

---

## What This Does NOT Do

- **Does not network-access VLR.gg** — the fixture is fully synthetic HTML
- **Does not require a database** — entirely in-memory
- **Does not produce live records** — all records are discarded after the check
- **Does not affect scheduled jobs** — `KnownRecordRegistry` skips `EXAMPLE_*` match IDs automatically

---

## Reference: Example Corpus Data Contract

| Property | Value |
|---|---|
| Fixture path | `extraction/fixtures/example_match.json` |
| Match ID | `EXAMPLE_000001` |
| `separation_flag` | `9` (sentinel — never used by live records) |
| Exclusion reason code | `EXAMPLE_DATA` |
| Numeric tolerance | ±5% |
| String matching | case-insensitive, whitespace-stripped |
| Must be discarded after check | Yes — `del records` |
| Safe to store in live DB | **Never** |
| Fixture version | `1.0.0` |

---

## Reference: Files Involved

| File | Role |
|---|---|
| `extraction/fixtures/example_match.json` | Committed fixture — the security-check baseline |
| `extraction/src/storage/example_corpus.py` | `ExampleCorpus` class — loads fixture, runs security check |
| `extraction/src/storage/known_record_registry.py` | `KnownRecordRegistry.should_skip()` — auto-skips `EXAMPLE_*` |
| `extraction/src/bridge/extraction_bridge.py` | `transform()` — auto-stamps `separation_flag=9` |
| `config/harvest_protocol.json` | Protocol contract — defines `EXAMPLE_DATA` reason code |
| `extraction/tests/test_example_corpus.py` | Tests — verify isolation guarantees |
| `docs/AGENT_RUNBOOK.md` | This document |
