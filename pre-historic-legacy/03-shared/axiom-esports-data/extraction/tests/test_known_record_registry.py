"""
Tests for KnownRecordRegistry and ExclusionList.

Validates:
  - Registry correctly classifies complete / excluded / pending match IDs
  - should_skip() prevents redundant fetches for known records
  - mark_complete() and mark_excluded() maintain consistent state
  - ExclusionList enforces reason code contract from harvest_protocol.json
  - PipelineBlockedError is raised for SCHEMA_CONFLICT entries
  - assert_pipeline_safe() gates the analytics pipeline
  - Coordinated harvester + registry integration (no scrape for known records)
"""
import asyncio
import pytest

from extraction.src.storage.known_record_registry import (
    KnownRecordRegistry,
    ExclusionEntry,
    RegistryStats,
)
from extraction.src.storage.exclusion_list import (
    ExclusionList,
    PipelineBlockedError,
)


# ---------------------------------------------------------------------------
# KnownRecordRegistry — unit tests (memory-only, no DB)
# ---------------------------------------------------------------------------

class TestKnownRecordRegistryBasics:
    def test_new_registry_is_empty(self):
        reg = KnownRecordRegistry(db_url=None)
        assert not reg.is_known("match_001")
        assert not reg.is_complete("match_001")
        assert not reg.is_excluded("match_001")

    def test_mark_complete_makes_it_known_and_complete(self):
        reg = KnownRecordRegistry(db_url=None)
        reg.mark_complete("match_001")
        assert reg.is_known("match_001")
        assert reg.is_complete("match_001")
        assert not reg.is_excluded("match_001")

    def test_mark_excluded_makes_it_known_and_excluded(self):
        reg = KnownRecordRegistry(db_url=None)
        reg.mark_excluded("match_002", reason_code="MANUAL_EXCLUDE", notes="test")
        assert reg.is_known("match_002")
        assert reg.is_excluded("match_002")
        assert not reg.is_complete("match_002")

    def test_add_pending_makes_it_known(self):
        reg = KnownRecordRegistry(db_url=None)
        reg.add_pending("match_003")
        assert reg.is_known("match_003")
        assert not reg.is_complete("match_003")
        assert not reg.is_excluded("match_003")
        assert "match_003" in reg.list_pending()

    def test_mark_complete_removes_from_pending(self):
        reg = KnownRecordRegistry(db_url=None)
        reg.add_pending("match_004")
        assert "match_004" in reg.list_pending()
        reg.mark_complete("match_004")
        assert "match_004" not in reg.list_pending()

    def test_mark_excluded_removes_from_pending(self):
        reg = KnownRecordRegistry(db_url=None)
        reg.add_pending("match_005")
        reg.mark_excluded("match_005", reason_code="DUPLICATE")
        assert "match_005" not in reg.list_pending()


class TestShouldSkip:
    def test_should_skip_unknown_returns_false(self):
        reg = KnownRecordRegistry(db_url=None)
        assert not reg.should_skip("unknown_match")

    def test_should_skip_complete_returns_true(self):
        reg = KnownRecordRegistry(db_url=None)
        reg.mark_complete("done_match")
        assert reg.should_skip("done_match")

    def test_should_skip_excluded_returns_true(self):
        reg = KnownRecordRegistry(db_url=None)
        reg.mark_excluded("bad_match", reason_code="SCHEMA_CONFLICT", notes="parser failed")
        assert reg.should_skip("bad_match")

    def test_should_skip_pending_returns_false(self):
        """Pending matches are known but not complete — they must be re-scraped."""
        reg = KnownRecordRegistry(db_url=None)
        reg.add_pending("pending_match")
        assert not reg.should_skip("pending_match")


class TestShouldSkipChecksum:
    def test_skip_on_unchanged_checksum(self):
        reg = KnownRecordRegistry(db_url=None)
        cs = "a" * 64
        reg.mark_complete("m1", checksum=cs)
        assert reg.should_skip_checksum("m1", cs)

    def test_no_skip_on_changed_checksum(self):
        reg = KnownRecordRegistry(db_url=None)
        reg.mark_complete("m2", checksum="a" * 64)
        assert not reg.should_skip_checksum("m2", "b" * 64)

    def test_no_skip_when_no_prior_checksum(self):
        reg = KnownRecordRegistry(db_url=None)
        assert not reg.should_skip_checksum("new_match", "c" * 64)


class TestReinstate:
    def test_reinstate_clears_exclusion(self):
        reg = KnownRecordRegistry(db_url=None)
        reg.mark_excluded("m3", reason_code="LOW_CONFIDENCE")
        assert reg.is_excluded("m3")
        reg.reinstate("m3")
        assert not reg.is_excluded("m3")

    def test_reinstated_match_becomes_pending(self):
        reg = KnownRecordRegistry(db_url=None)
        reg.mark_excluded("m4", reason_code="CONTENT_DRIFT")
        reg.reinstate("m4")
        assert "m4" in reg.list_pending()


class TestRegistryStats:
    def test_stats_reflect_correct_counts(self):
        reg = KnownRecordRegistry(db_url=None)
        reg.mark_complete("c1")
        reg.mark_complete("c2")
        reg.add_pending("p1")
        reg.mark_excluded("e1", reason_code="DUPLICATE")
        stats = reg.get_stats()
        assert stats.complete == 2
        assert stats.pending == 1
        assert stats.excluded == 1
        assert stats.total_known == 4

    def test_skip_rate_positive(self):
        reg = KnownRecordRegistry(db_url=None)
        reg.mark_complete("c1")
        reg.mark_excluded("e1", reason_code="MANUAL_EXCLUDE")
        reg.add_pending("p1")
        stats = reg.get_stats()
        d = stats.as_dict()
        assert 0.0 < d["skip_rate_pct"] <= 100.0


class TestInvalidExclusionReason:
    def test_invalid_reason_raises_value_error(self):
        reg = KnownRecordRegistry(db_url=None)
        with pytest.raises(ValueError, match="Unknown exclusion reason"):
            reg.mark_excluded("mx", reason_code="NOT_A_REAL_REASON")


# ---------------------------------------------------------------------------
# ExclusionList — unit tests
# ---------------------------------------------------------------------------

class TestExclusionListBasics:
    def test_empty_list_is_safe(self, tmp_path):
        xl = ExclusionList(runtime_path=tmp_path / "ex.json", committed_path=tmp_path / "committed.json")
        xl.assert_pipeline_safe()  # should not raise

    def test_add_and_is_excluded(self, tmp_path):
        xl = ExclusionList(runtime_path=tmp_path / "ex.json", committed_path=tmp_path / "committed.json")
        xl.add("m_dup", reason_code="DUPLICATE", notes="same as m_orig")
        assert xl.is_excluded("m_dup")

    def test_add_unknown_reason_raises(self, tmp_path):
        xl = ExclusionList(runtime_path=tmp_path / "ex.json", committed_path=tmp_path / "committed.json")
        with pytest.raises(ValueError, match="Unknown exclusion reason"):
            xl.add("mx", reason_code="FAKE_CODE")

    def test_schema_conflict_raises_pipeline_blocked(self, tmp_path):
        xl = ExclusionList(runtime_path=tmp_path / "ex.json", committed_path=tmp_path / "committed.json")
        with pytest.raises(PipelineBlockedError):
            xl.add("m_bad", reason_code="SCHEMA_CONFLICT", notes="parser broke")

    def test_assert_pipeline_safe_raises_when_blocked(self, tmp_path):
        xl = ExclusionList(runtime_path=tmp_path / "ex.json", committed_path=tmp_path / "committed.json")
        try:
            xl.add("m_sc", reason_code="SCHEMA_CONFLICT", notes="drift")
        except PipelineBlockedError:
            pass  # Expected on add
        with pytest.raises(PipelineBlockedError):
            xl.assert_pipeline_safe()

    def test_reinstate_clears_exclusion(self, tmp_path):
        xl = ExclusionList(runtime_path=tmp_path / "ex.json", committed_path=tmp_path / "committed.json")
        xl.add("m_low", reason_code="LOW_CONFIDENCE", notes="below floor")
        assert xl.is_excluded("m_low")
        xl.reinstate("m_low")
        assert not xl.is_excluded("m_low")

    def test_list_for_review_returns_auto_review(self, tmp_path):
        xl = ExclusionList(runtime_path=tmp_path / "ex.json", committed_path=tmp_path / "committed.json")
        xl.add("m_drift", reason_code="CONTENT_DRIFT", notes="5.1% diff")
        xl.add("m_dup", reason_code="DUPLICATE", notes="dupe")
        review = xl.list_for_review()
        ids = [e.match_id for e in review]
        assert "m_drift" in ids
        assert "m_dup" not in ids  # DUPLICATE is not AUTO_REVIEW

    def test_summary_counts_by_reason(self, tmp_path):
        xl = ExclusionList(runtime_path=tmp_path / "ex.json", committed_path=tmp_path / "committed.json")
        xl.add("m1", reason_code="DUPLICATE")
        xl.add("m2", reason_code="DUPLICATE")
        xl.add("m3", reason_code="LOW_CONFIDENCE")
        s = xl.summary()
        assert s["total_excluded"] == 3
        assert s["by_reason"]["DUPLICATE"] == 2
        assert s["by_reason"]["LOW_CONFIDENCE"] == 1

    def test_persistence_round_trip(self, tmp_path):
        rt = tmp_path / "ex.json"
        ct = tmp_path / "committed.json"
        xl1 = ExclusionList(runtime_path=rt, committed_path=ct)
        xl1.add("persist_me", reason_code="MANUAL_EXCLUDE", notes="round trip test")
        # Load a fresh instance from the same file
        xl2 = ExclusionList(runtime_path=rt, committed_path=ct)
        assert xl2.is_excluded("persist_me")


# ---------------------------------------------------------------------------
# Coordinated harvester + registry integration
# ---------------------------------------------------------------------------

class TestHarvesterRegistryIntegration:
    @pytest.mark.asyncio
    async def test_harvester_skips_complete_matches(self):
        """Known-complete matches must not result in any network fetch."""
        import aiohttp
        from extraction.src.scrapers.epoch_harvester import EpochHarvester, EPOCHS
        from extraction.src.scrapers.vlr_resilient_client import ResilientVLRClient

        registry = KnownRecordRegistry(db_url=None)
        registry.mark_complete("match_already_done", checksum="a" * 64)

        harvester = EpochHarvester(mode="delta", registry=registry)

        # Inject match_already_done into the pending queue the harvester would process
        async def _fake_get_ids(epoch_num, config):
            return ["match_already_done", "also_known"]

        harvester._get_target_match_ids = _fake_get_ids
        registry.mark_complete("also_known")

        async with aiohttp.ClientSession() as session:
            client = ResilientVLRClient(session=session)
            count = await harvester.harvest_epoch(1, client)

        # Both matches were skipped — nothing was stored
        assert count == 0

    @pytest.mark.asyncio
    async def test_harvester_skips_excluded_matches(self):
        """Excluded matches must not be fetched even in full mode."""
        import aiohttp
        from extraction.src.scrapers.epoch_harvester import EpochHarvester
        from extraction.src.scrapers.vlr_resilient_client import ResilientVLRClient

        registry = KnownRecordRegistry(db_url=None)
        registry.mark_excluded("bad_match", reason_code="SCHEMA_CONFLICT", notes="drift")

        harvester = EpochHarvester(mode="full", registry=registry)

        async def _fake_get_ids(epoch_num, config):
            return ["bad_match"]

        harvester._get_target_match_ids = _fake_get_ids

        async with aiohttp.ClientSession() as session:
            client = ResilientVLRClient(session=session)
            count = await harvester.harvest_epoch(2, client)

        assert count == 0
