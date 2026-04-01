#!/usr/bin/env python
"""
agent_security_check.py — Run the pipeline security check against the committed fixture.

This script MUST be run by any new agent or engineer before performing live scraping.
It verifies that the extraction pipeline (MatchParser → ExtractionBridge) produces
correct output by comparing against the committed example fixture.

Exit code 0 = PASSED (safe to proceed with live scraping)
Exit code 1 = FAILED (fix the pipeline before proceeding)

Usage
-----
    cd axiom-esports-data
    python scripts/agent_security_check.py

See docs/AGENT_RUNBOOK.md for a complete step-by-step guide and troubleshooting.
"""
import logging
import sys
from pathlib import Path

# Allow running from the axiom-esports-data/ directory
_HERE = Path(__file__).parent.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    from extraction.src.storage.example_corpus import ExampleCorpus
    from extraction.src.parsers.match_parser import MatchParser
    from extraction.src.bridge.extraction_bridge import ExtractionBridge

    print("=" * 64)
    print("SATOR Pipeline Security Check")
    print("=" * 64)

    corpus = ExampleCorpus()

    # ── Step 1: Load fixture ──────────────────────────────────────────
    try:
        fixture = corpus.load_fixture()
    except FileNotFoundError as exc:
        logger.error("Fixture not found: %s", exc)
        return 1
    except ValueError as exc:
        logger.error("Malformed fixture: %s", exc)
        return 1

    print(f"\n✓ Fixture loaded  (version={fixture['fixture_version']}, "
          f"created_by={fixture['created_by']})")

    # ── Step 2: Get example HTML ──────────────────────────────────────
    html, match_id = corpus.get_example_html()
    print(f"✓ HTML extracted  (match_id={match_id}, length={len(html)} chars)")

    # ── Step 3: Parse ─────────────────────────────────────────────────
    parser = MatchParser()
    raw = parser.parse(html, match_id)
    if raw is None:
        logger.error("MatchParser returned None — schema validation failed.")
        logger.error("Check that the fixture HTML contains: vm-stats-game, mod-player, mod-stat")
        return 1

    print(f"✓ Parse OK        ({len(raw.players)} players, map={raw.map_name}, "
          f"patch={raw.patch_version})")

    # ── Step 4: Translate ─────────────────────────────────────────────
    bridge = ExtractionBridge()
    records = bridge.transform(raw)

    bad_flags = [r for r in records if r.separation_flag != 9]
    if bad_flags:
        logger.error(
            "%d record(s) have separation_flag != 9 — isolation is broken!",
            len(bad_flags),
        )
        return 1

    print(f"✓ Bridge OK       ({len(records)} KCRITRRecords, all separation_flag=9)")

    # ── Step 5: Security check ────────────────────────────────────────
    result = corpus.security_check(raw, records)

    print("\n" + "-" * 64)
    print(result.summary())
    print("-" * 64)

    if not result.passed:
        print("\nFailures:")
        for failure in result.failures:
            print(f"  ✗ {failure}")
        print(
            "\n⚠  Security check FAILED.\n"
            "   Fix the pipeline before running live scraping.\n"
            "   See docs/AGENT_RUNBOOK.md for troubleshooting.\n"
        )
        return 1

    # ── Step 6: Discard ───────────────────────────────────────────────
    del records  # CRITICAL — do NOT store example records in the live DB
    print(
        "\n✓ Example records DISCARDED (not stored in DB — this is correct).\n"
        "✓ Pipeline is VERIFIED. Safe to proceed with live scraping.\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
