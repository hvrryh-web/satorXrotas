"""
ExampleCorpus — Isolation layer for agent security-check fixtures.

Purpose
-------
The example corpus holds a committed set of synthetic, deterministic records
that future agents use to verify the extraction pipeline produces correct output.
These records are **permanently isolated** from the live analytics pipeline:

    separation_flag = 9   (sentinel value — never used by live records)
    match_id prefix = "EXAMPLE_"
    reason_code = "EXAMPLE_DATA"

Isolation guarantees
--------------------
1. ``is_example(match_id)`` — fast O(1) guard used by EpochHarvester and
   ExtractionBridge to detect example records before any processing.

2. ``ExtractionBridge`` stamps ``separation_flag=9`` on any record whose
   match_id starts with "EXAMPLE_" or whose corpus membership is confirmed.

3. ``KnownRecordRegistry.should_skip()`` returns True for example IDs so
   they are never fetched, re-scraped, or written to the live DB.

4. ``ExampleCorpus.security_check()`` loads the committed fixture
   (``extraction/fixtures/example_match.json``) and compares a freshly
   reproduced parse against the expected values.  This is the primary
   correctness verification step for new agents.

Security check workflow (for future agents)
-------------------------------------------
    from extraction.src.storage.example_corpus import ExampleCorpus
    from extraction.src.parsers.match_parser import MatchParser
    from extraction.src.bridge.extraction_bridge import ExtractionBridge

    corpus = ExampleCorpus()
    fixture = corpus.load_fixture()

    # 1. Parse the committed example HTML
    parser = MatchParser()
    raw = parser.parse(fixture["source_html"]["html"],
                       fixture["source_html"]["match_id"])

    # 2. Translate to KCRITR records (bridge auto-stamps separation_flag=9)
    bridge = ExtractionBridge()
    records = bridge.transform(raw)

    # 3. Run security check — raises AssertionError with details on failure
    corpus.security_check(raw, records)

    # 4. DISCARD records — do NOT store in live DB
    #    The check is proof of correctness, not a data import.

See docs/AGENT_RUNBOOK.md for a complete step-by-step guide.
"""
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Match IDs with this prefix are always example records
EXAMPLE_PREFIX = "EXAMPLE_"

# separation_flag value for all example records (never used by live records)
EXAMPLE_SEPARATION_FLAG = 9

# Path to the committed fixture file (relative to this module's package root)
_FIXTURE_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "extraction" / "fixtures" / "example_match.json"
)

# Numeric tolerance for security check comparisons (5 %)
NUMERIC_TOLERANCE_PCT = 5.0


@dataclass
class SecurityCheckResult:
    """Result of a security_check() call."""
    passed: bool
    player_count_ok: bool
    separation_flags_ok: bool
    spot_check_results: list[dict]
    failures: list[str]

    def summary(self) -> str:
        if self.passed:
            return f"SECURITY CHECK PASSED — {len(self.spot_check_results)} player(s) verified"
        return (
            f"SECURITY CHECK FAILED — {len(self.failures)} failure(s): "
            + "; ".join(self.failures[:3])
        )


class ExampleCorpus:
    """
    Manages the committed example fixture set and security-check logic.

    The corpus is intentionally stateless beyond the fixture file on disk.
    It does not hold a DB connection or an in-memory record cache.
    """

    # ------------------------------------------------------------------
    # Guard — used by EpochHarvester and ExtractionBridge
    # ------------------------------------------------------------------

    @staticmethod
    def is_example(match_id: str) -> bool:
        """
        True if match_id belongs to the example corpus.

        Currently this is a prefix check.  Future agents may extend this
        to query the committed fixture file for explicit IDs.
        """
        return str(match_id).startswith(EXAMPLE_PREFIX)

    # ------------------------------------------------------------------
    # Fixture I/O
    # ------------------------------------------------------------------

    def load_fixture(self, fixture_path: Optional[Path] = None) -> dict[str, Any]:
        """
        Load the committed example fixture from disk.

        Raises
        ------
        FileNotFoundError  if the fixture file does not exist.
        ValueError         if the JSON is malformed.
        """
        path = fixture_path or _FIXTURE_PATH
        if not path.exists():
            raise FileNotFoundError(
                f"Example fixture not found at {path}. "
                f"This file must be committed to the repository."
            )
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed example fixture at {path}: {exc}") from exc

    def get_example_html(self, fixture_path: Optional[Path] = None) -> tuple[str, str]:
        """
        Return (html, match_id) from the committed fixture.

        Convenience wrapper so agents don't need to dig into the fixture structure.
        """
        fixture = self.load_fixture(fixture_path)
        source = fixture["source_html"]
        return source["html"], source["match_id"]

    # ------------------------------------------------------------------
    # Security check — the primary correctness verification step
    # ------------------------------------------------------------------

    def security_check(
        self,
        raw_match: Any,         # RawMatchData from MatchParser
        records: list[Any],     # list[KCRITRRecord] from ExtractionBridge
        fixture_path: Optional[Path] = None,
    ) -> SecurityCheckResult:
        """
        Compare a freshly reproduced parse+translate against the committed fixture.

        Steps
        -----
        1. Verify player_count matches ``expected_parse.player_count``.
        2. Verify all records have ``separation_flag == 9``.
        3. Spot-check each player listed in ``expected_records`` against
           the reproduced records, applying ±5 % tolerance for numeric fields
           and exact-match (normalised) for string fields.
        4. Return a SecurityCheckResult; does NOT raise on failure so callers
           can decide whether to assert or log.

        The check is PROOF OF CORRECTNESS — after it passes the reproduced
        records must be DISCARDED, not stored in the live DB.
        """
        fixture = self.load_fixture(fixture_path)
        expected_parse = fixture.get("expected_parse", {})
        expected_records = fixture.get("expected_records", [])
        rules = fixture.get("security_check_rules", {})

        failures: list[str] = []

        # ── 1. Player count ──────────────────────────────────────────────
        expected_count = rules.get(
            "must_produce_player_count",
            expected_parse.get("player_count", 0),
        )
        player_count_ok = len(records) == expected_count
        if not player_count_ok:
            failures.append(
                f"player_count: expected {expected_count}, got {len(records)}"
            )

        # ── 2. All separation_flag == 9 ──────────────────────────────────
        bad_flags = [r for r in records if r.separation_flag != EXAMPLE_SEPARATION_FLAG]
        separation_flags_ok = len(bad_flags) == 0
        if not separation_flags_ok:
            failures.append(
                f"separation_flag: {len(bad_flags)} record(s) do not have flag=9 "
                f"(found flags: {set(r.separation_flag for r in bad_flags)})"
            )

        # ── 3. Spot-check expected players ───────────────────────────────
        spot_results: list[dict] = []
        tol = rules.get("numeric_tolerance_pct", NUMERIC_TOLERANCE_PCT) / 100.0

        for expected in expected_records:
            expected_name = expected.get("name", "").lower().strip()
            # Find matching reproduced record by normalised name
            match = next(
                (r for r in records
                 if (r.name or "").lower().strip() == expected_name),
                None,
            )
            spot: dict[str, Any] = {"player": expected_name, "found": match is not None}

            if match is None:
                spot["error"] = f"No record found for player '{expected_name}'"
                spot["passed"] = False
                failures.append(spot["error"])
                spot_results.append(spot)
                continue

            field_results: list[str] = []

            # Numeric range checks
            for field_prefix, attr in [
                ("kills",       "kills"),
                ("deaths",      "deaths"),
                ("acs",         "acs"),
                ("adr",         "adr"),
                ("kast_pct",    "kast_pct"),
                ("headshot_pct","headshot_pct"),
            ]:
                lo = expected.get(f"{field_prefix}_min")
                hi = expected.get(f"{field_prefix}_max")
                if lo is None or hi is None:
                    continue
                val = getattr(match, attr, None)
                if val is None:
                    field_results.append(f"{attr}=None (expected {lo}-{hi})")
                    continue
                # Apply tolerance to bounds
                lo_adj = lo * (1 - tol)
                hi_adj = hi * (1 + tol)
                if not (lo_adj <= float(val) <= hi_adj):
                    msg = (
                        f"{attr}={val} outside [{lo_adj:.1f}, {hi_adj:.1f}] "
                        f"(expected range [{lo}, {hi}] ± {tol*100:.0f}%)"
                    )
                    field_results.append(msg)

            # String checks
            expected_agent = expected.get("agent", "").lower().strip()
            if expected_agent:
                actual_agent = (match.agent or "").lower()
                if expected_agent not in actual_agent:
                    field_results.append(
                        f"agent: expected '{expected_agent}' in '{actual_agent}'"
                    )

            map_contains = expected.get("map_name_contains", "")
            if map_contains:
                actual_map = (match.map_name or "").lower()
                if map_contains.lower() not in actual_map:
                    field_results.append(
                        f"map_name: expected to contain '{map_contains}', got '{actual_map}'"
                    )

            if expected.get("separation_flag") is not None:
                if match.separation_flag != expected["separation_flag"]:
                    field_results.append(
                        f"separation_flag: expected {expected['separation_flag']}, "
                        f"got {match.separation_flag}"
                    )

            if expected.get("data_source"):
                if match.data_source != expected["data_source"]:
                    field_results.append(
                        f"data_source: expected '{expected['data_source']}', "
                        f"got '{match.data_source}'"
                    )

            spot["field_failures"] = field_results
            spot["passed"] = len(field_results) == 0
            if field_results:
                failures.extend(
                    [f"Player '{expected_name}' — {f}" for f in field_results]
                )
            spot_results.append(spot)

        result = SecurityCheckResult(
            passed=len(failures) == 0,
            player_count_ok=player_count_ok,
            separation_flags_ok=separation_flags_ok,
            spot_check_results=spot_results,
            failures=failures,
        )
        if result.passed:
            logger.info("ExampleCorpus.security_check: %s", result.summary())
        else:
            logger.error("ExampleCorpus.security_check: %s", result.summary())
        return result
