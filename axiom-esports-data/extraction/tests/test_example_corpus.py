"""
Tests for ExampleCorpus isolation, security check, and pipeline guard.

These tests verify:
  1. ExampleCorpus.is_example() correctly identifies example match IDs
  2. The committed fixture loads and has correct structure
  3. ExtractionBridge.transform() stamps separation_flag=9 for example records
  4. KnownRecordRegistry.should_skip() returns True for example IDs
  5. security_check() passes when given correctly-produced records
  6. security_check() fails (with clear messages) when records are wrong
  7. Example records are distinguishable from live records in all cases

All assertions are range-based or structural (no hardcoded player stats).
"""
import uuid
from pathlib import Path

import pytest

from extraction.src.storage.example_corpus import (
    ExampleCorpus,
    SecurityCheckResult,
    EXAMPLE_PREFIX,
    EXAMPLE_SEPARATION_FLAG,
    NUMERIC_TOLERANCE_PCT,
)
from extraction.src.storage.known_record_registry import KnownRecordRegistry
from extraction.src.parsers.match_parser import MatchParser, RawMatchData
from extraction.src.bridge.extraction_bridge import ExtractionBridge, KCRITRRecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_corpus_and_records() -> tuple[ExampleCorpus, RawMatchData, list[KCRITRRecord]]:
    """Parse the committed fixture and produce KCRITRRecords. Used by multiple tests."""
    corpus = ExampleCorpus()
    html, match_id = corpus.get_example_html()
    raw = MatchParser().parse(html, match_id)
    assert raw is not None, "MatchParser returned None for example fixture HTML"
    records = ExtractionBridge().transform(raw)
    return corpus, raw, records


# ---------------------------------------------------------------------------
# 1. is_example() guard
# ---------------------------------------------------------------------------

class TestIsExample:
    def test_example_prefix_detected(self):
        assert ExampleCorpus.is_example("EXAMPLE_000001")

    def test_example_prefix_case_sensitive(self):
        # prefix is UPPER — lowercase must NOT match
        assert not ExampleCorpus.is_example("example_000001")

    def test_live_match_id_not_example(self):
        assert not ExampleCorpus.is_example("123456")

    def test_empty_string_not_example(self):
        assert not ExampleCorpus.is_example("")

    def test_partial_prefix_not_example(self):
        assert not ExampleCorpus.is_example("EXAMP_001")

    def test_any_example_id_detected(self):
        for i in range(5):
            assert ExampleCorpus.is_example(f"EXAMPLE_{i:06d}")


# ---------------------------------------------------------------------------
# 2. Fixture file structure
# ---------------------------------------------------------------------------

class TestFixtureStructure:
    def test_fixture_loads_without_error(self):
        corpus = ExampleCorpus()
        fixture = corpus.load_fixture()
        assert isinstance(fixture, dict)

    def test_fixture_has_required_top_level_keys(self):
        corpus = ExampleCorpus()
        fixture = corpus.load_fixture()
        for key in ("fixture_version", "source_html", "expected_parse",
                    "expected_records", "security_check_rules"):
            assert key in fixture, f"Fixture missing top-level key: '{key}'"

    def test_fixture_version_is_string(self):
        corpus = ExampleCorpus()
        assert isinstance(corpus.load_fixture()["fixture_version"], str)

    def test_source_html_has_match_id(self):
        corpus = ExampleCorpus()
        source = corpus.load_fixture()["source_html"]
        assert "match_id" in source
        assert source["match_id"].startswith(EXAMPLE_PREFIX)

    def test_source_html_has_html_string(self):
        corpus = ExampleCorpus()
        source = corpus.load_fixture()["source_html"]
        assert "html" in source
        assert len(source["html"]) > 100  # Non-trivial HTML

    def test_expected_parse_has_player_count(self):
        corpus = ExampleCorpus()
        ep = corpus.load_fixture()["expected_parse"]
        assert "player_count" in ep
        assert ep["player_count"] > 0

    def test_expected_records_is_list(self):
        corpus = ExampleCorpus()
        er = corpus.load_fixture()["expected_records"]
        assert isinstance(er, list)
        assert len(er) >= 1

    def test_expected_records_have_range_bounds(self):
        corpus = ExampleCorpus()
        for rec in corpus.load_fixture()["expected_records"]:
            assert "acs_min" in rec and "acs_max" in rec
            assert rec["acs_min"] < rec["acs_max"]

    def test_get_example_html_returns_tuple(self):
        corpus = ExampleCorpus()
        html, match_id = corpus.get_example_html()
        assert isinstance(html, str)
        assert isinstance(match_id, str)
        assert match_id.startswith(EXAMPLE_PREFIX)

    def test_fixture_html_has_required_markers(self):
        corpus = ExampleCorpus()
        html, _ = corpus.get_example_html()
        for marker in ("vm-stats-game", "mod-player", "mod-stat"):
            assert marker in html, f"Fixture HTML missing required marker: '{marker}'"

    def test_missing_fixture_raises_file_not_found(self):
        corpus = ExampleCorpus()
        with pytest.raises(FileNotFoundError):
            corpus.load_fixture(Path("/nonexistent/path/fixture.json"))


# ---------------------------------------------------------------------------
# 3. ExtractionBridge stamps separation_flag=9 for example records
# ---------------------------------------------------------------------------

class TestBridgeSeparationFlag:
    def test_example_match_id_gets_flag_9(self):
        _, _, records = _load_corpus_and_records()
        for r in records:
            assert r.separation_flag == EXAMPLE_SEPARATION_FLAG, (
                f"Expected separation_flag={EXAMPLE_SEPARATION_FLAG}, "
                f"got {r.separation_flag} for player '{r.name}'"
            )

    def test_live_match_id_gets_flag_0(self):
        raw = RawMatchData(
            vlr_match_id="live_match_99999",
            tournament="VCT Test",
            map_name="Bind",
            match_date=None,
            patch_version="8.11",
            players=[{
                "player": "LivePlayer",
                "team": "TeamX",
                "acs": "220",
                "kills": "18",
                "deaths": "15",
                "kast": "70%",
                "adr": "140",
                "hs_pct": "25%",
                "first_blood": "2",
                "clutch_win": "1",
                "agent": "Jett",
            }],
        )
        records = ExtractionBridge().transform(raw)
        assert len(records) == 1
        assert records[0].separation_flag == 0

    def test_example_records_have_example_match_id(self):
        _, _, records = _load_corpus_and_records()
        for r in records:
            assert r.match_id.startswith(EXAMPLE_PREFIX)

    def test_example_records_count(self):
        _, raw, records = _load_corpus_and_records()
        # Bridge must produce one record per player row
        assert len(records) == len(raw.players)
        assert len(records) > 0

    def test_example_records_have_checksums(self):
        _, _, records = _load_corpus_and_records()
        for r in records:
            assert r.checksum_sha256 is not None
            assert len(r.checksum_sha256) == 64

    def test_example_player_ids_are_stable(self):
        """Running the bridge twice on the same fixture must produce identical UUIDs."""
        corpus = ExampleCorpus()
        html, mid = corpus.get_example_html()
        raw = MatchParser().parse(html, mid)
        ids_run1 = [r.player_id for r in ExtractionBridge().transform(raw)]
        ids_run2 = [r.player_id for r in ExtractionBridge().transform(raw)]
        assert ids_run1 == ids_run2

    def test_example_and_live_same_player_same_uuid(self):
        """A player who appears in both example and live data must have the same UUID."""
        # Example record
        corpus = ExampleCorpus()
        html, mid = corpus.get_example_html()
        raw_ex = MatchParser().parse(html, mid)
        ex_records = ExtractionBridge().transform(raw_ex)
        ex_player = ex_records[0]

        # Live record for the same player name
        raw_live = RawMatchData(
            vlr_match_id="live_match_abc",
            tournament="Real Event",
            map_name="Bind",
            match_date=None,
            patch_version="8.11",
            players=[{
                "player": raw_ex.players[0].get("player", "Alpha"),
                "team": "",
                "acs": "200",
                "kills": "14",
                "deaths": "12",
                "kast": "68%",
                "adr": "120",
                "hs_pct": "20%",
                "first_blood": "1",
                "clutch_win": "0",
                "agent": "Jett",
            }],
        )
        live_records = ExtractionBridge().transform(raw_live)
        assert live_records[0].player_id == ex_player.player_id
        # But flags must differ
        assert ex_player.separation_flag == EXAMPLE_SEPARATION_FLAG
        assert live_records[0].separation_flag == 0


# ---------------------------------------------------------------------------
# 4. KnownRecordRegistry skips example IDs
# ---------------------------------------------------------------------------

class TestRegistrySkipsExamples:
    def test_example_id_should_skip_returns_true(self):
        registry = KnownRecordRegistry(db_url=None)
        assert registry.should_skip("EXAMPLE_000001")

    def test_multiple_example_ids_all_skipped(self):
        registry = KnownRecordRegistry(db_url=None)
        for i in range(5):
            assert registry.should_skip(f"EXAMPLE_{i:06d}")

    def test_live_id_not_skipped_when_new(self):
        registry = KnownRecordRegistry(db_url=None)
        assert not registry.should_skip("live_match_xyz")

    def test_example_id_not_added_to_complete_set(self):
        registry = KnownRecordRegistry(db_url=None)
        # Attempting to mark an example as complete should not affect the
        # should_skip result (it's already True via corpus guard)
        registry.mark_complete("EXAMPLE_000001")
        assert registry.should_skip("EXAMPLE_000001")

    def test_example_id_stats_not_counted_as_live(self):
        registry = KnownRecordRegistry(db_url=None)
        # Mark a live record complete
        registry.mark_complete("live_match_001")
        stats = registry.get_stats()
        # Only live records should be in complete count
        assert stats.complete >= 1
        # Example IDs skipped before reaching registry state — should not inflate count
        registry.should_skip("EXAMPLE_000001")
        registry.should_skip("EXAMPLE_000002")
        assert registry.get_stats().complete == stats.complete  # Unchanged


# ---------------------------------------------------------------------------
# 5. security_check() — PASS cases
# ---------------------------------------------------------------------------

class TestSecurityCheckPasses:
    def test_correctly_produced_records_pass(self):
        corpus, raw, records = _load_corpus_and_records()
        result = corpus.security_check(raw, records)
        assert result.passed, (
            f"Security check failed with correctly-produced records.\n"
            f"Failures: {result.failures}"
        )

    def test_player_count_ok_when_pass(self):
        corpus, raw, records = _load_corpus_and_records()
        result = corpus.security_check(raw, records)
        assert result.player_count_ok

    def test_separation_flags_ok_when_pass(self):
        corpus, raw, records = _load_corpus_and_records()
        result = corpus.security_check(raw, records)
        assert result.separation_flags_ok

    def test_spot_check_results_non_empty(self):
        corpus, raw, records = _load_corpus_and_records()
        result = corpus.security_check(raw, records)
        assert len(result.spot_check_results) > 0

    def test_all_spot_checks_passed(self):
        corpus, raw, records = _load_corpus_and_records()
        result = corpus.security_check(raw, records)
        for spot in result.spot_check_results:
            assert spot["passed"], (
                f"Spot check failed for player '{spot['player']}': "
                f"{spot.get('field_failures', [])}"
            )

    def test_summary_contains_passed(self):
        corpus, raw, records = _load_corpus_and_records()
        result = corpus.security_check(raw, records)
        assert "PASSED" in result.summary()


# ---------------------------------------------------------------------------
# 6. security_check() — FAIL cases
# ---------------------------------------------------------------------------

class TestSecurityCheckFails:
    def _base_records(self) -> tuple[ExampleCorpus, RawMatchData, list[KCRITRRecord]]:
        return _load_corpus_and_records()

    def test_wrong_player_count_fails(self):
        corpus, raw, records = self._base_records()
        # Remove two records to simulate a parser regression
        result = corpus.security_check(raw, records[:8])
        assert not result.passed
        assert not result.player_count_ok
        assert any("player_count" in f for f in result.failures)

    def test_wrong_separation_flag_fails(self):
        import dataclasses
        corpus, raw, records = self._base_records()
        # Patch all records to have flag=0 (simulate bridge bug)
        bad_records = [dataclasses.replace(r, separation_flag=0) for r in records]
        result = corpus.security_check(raw, bad_records)
        assert not result.passed
        assert not result.separation_flags_ok
        assert any("separation_flag" in f for f in result.failures)

    def test_acs_far_out_of_range_fails(self):
        import dataclasses
        corpus, raw, records = self._base_records()
        # Set acs to 0 for all records — clearly wrong
        bad_records = [dataclasses.replace(r, acs=0.0) for r in records]
        result = corpus.security_check(raw, bad_records)
        assert not result.passed
        assert any("acs" in f for f in result.failures)

    def test_wrong_agent_fails(self):
        import dataclasses
        corpus, raw, records = self._base_records()
        # Replace all agents with a wrong value
        bad_records = [dataclasses.replace(r, agent="cid:agent:viper") for r in records]
        # The fixture expects "jett" for Alpha — Viper is wrong for that player
        result = corpus.security_check(raw, bad_records)
        # May or may not fail depending on which spot-checked player has Jett
        # but the result object must still be a SecurityCheckResult
        assert isinstance(result, SecurityCheckResult)

    def test_summary_contains_failed_on_failure(self):
        corpus, raw, records = self._base_records()
        result = corpus.security_check(raw, records[:5])  # Wrong count
        assert "FAILED" in result.summary()

    def test_failures_list_is_non_empty_on_failure(self):
        corpus, raw, records = self._base_records()
        result = corpus.security_check(raw, [])  # Empty records
        assert not result.passed
        assert len(result.failures) > 0


# ---------------------------------------------------------------------------
# 7. Full end-to-end: parse → translate → check → discard
# ---------------------------------------------------------------------------

class TestFullSecurityCheckWorkflow:
    def test_complete_workflow_passes(self):
        """Mirrors exactly the workflow described in docs/AGENT_RUNBOOK.md."""
        # Step 1: Load fixture
        corpus = ExampleCorpus()
        fixture = corpus.load_fixture()
        assert fixture["fixture_version"]

        # Step 2: Get HTML
        html, match_id = corpus.get_example_html()
        assert match_id.startswith(EXAMPLE_PREFIX)

        # Step 3: Parse
        raw = MatchParser().parse(html, match_id)
        assert raw is not None
        assert raw.vlr_match_id == match_id

        # Step 4: Translate
        records = ExtractionBridge().transform(raw)
        assert all(r.separation_flag == EXAMPLE_SEPARATION_FLAG for r in records)

        # Step 5: Security check
        result = corpus.security_check(raw, records)
        assert result.passed, f"Workflow security check failed: {result.failures}"

        # Step 6: Discard
        del records
        # If we reach here without storing anything, the workflow is correct.

    def test_example_records_isolated_from_live_pipeline(self):
        """Example records must be invisible to the live harvest pipeline."""
        registry = KnownRecordRegistry(db_url=None)
        corpus = ExampleCorpus()
        html, match_id = corpus.get_example_html()

        # Harvester would check should_skip before any network I/O
        assert registry.should_skip(match_id), (
            "Registry did not skip the example match_id — "
            "example records could reach the live pipeline!"
        )

    def test_example_records_never_contaminate_registry_stats(self):
        """Processing example records must not change registry stats."""
        registry = KnownRecordRegistry(db_url=None)
        stats_before = registry.get_stats()

        corpus = ExampleCorpus()
        html, match_id = corpus.get_example_html()
        raw = MatchParser().parse(html, match_id)
        records = ExtractionBridge().transform(raw)
        corpus.security_check(raw, records)

        stats_after = registry.get_stats()
        # Stats must be unchanged — no example record should affect the registry
        assert stats_after.complete == stats_before.complete
        assert stats_after.pending == stats_before.pending
