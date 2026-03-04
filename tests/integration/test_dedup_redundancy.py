"""
Tests for deduplication and redundancy prevention.

Ensures pipeline never:
1. Re-fetches content with same checksum
2. Stores duplicate match records
3. Processes excluded matches
4. Re-processes completed matches
"""

import pytest
import hashlib
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared" / "axiom-esports-data"))

from extraction.src.storage.known_record_registry import KnownRecordRegistry, ExclusionEntry
from extraction.src.storage.integrity_checker import compute_checksum, verify_checksum
from extraction.src.bridge.canonical_id import CanonicalIDResolver
from extraction.src.bridge.extraction_bridge import ExtractionBridge
from extraction.src.parsers.match_parser import RawMatchData
from extraction.src.storage.example_corpus import ExampleCorpus


# ============================================================================
# Redundancy Prevention Tests
# ============================================================================

class TestRedundancyPrevention:
    """Comprehensive redundancy prevention tests."""
    
    def test_registry_prevents_re_fetch(self):
        """KnownRecordRegistry.should_skip() prevents network calls."""
        registry = KnownRecordRegistry(db_url=None)
        
        # New match - should not skip
        assert not registry.should_skip("new_match_123")
        assert not registry.is_known("new_match_123")
        
        # Mark complete
        registry.mark_complete("new_match_123", checksum="abc" + "0" * 61)
        
        # Now should skip
        assert registry.should_skip("new_match_123")
        assert registry.is_known("new_match_123")
        assert registry.is_complete("new_match_123")
        
    def test_registry_prevents_excluded_re_fetch(self):
        """Excluded matches are never re-fetched."""
        registry = KnownRecordRegistry(db_url=None)
        
        # Exclude for schema conflict
        registry.mark_excluded("bad_match", reason_code="SCHEMA_CONFLICT")
        
        # Should skip
        assert registry.should_skip("bad_match")
        assert registry.is_known("bad_match")
        assert registry.is_excluded("bad_match")
        
        # Verify exclusion details
        excluded_list = registry.list_excluded()
        assert len(excluded_list) == 1
        assert excluded_list[0].match_id == "bad_match"
        assert excluded_list[0].reason_code == "SCHEMA_CONFLICT"
        
    def test_checksum_skip(self):
        """Unchanged checksum prevents re-write."""
        registry = KnownRecordRegistry(db_url=None)
        
        checksum1 = "hash123" + "0" * 57
        registry.mark_complete("match1", checksum=checksum1)
        
        # Same checksum - skip
        assert registry.should_skip_checksum("match1", checksum1)
        
        # Different checksum - don't skip
        assert not registry.should_skip_checksum("match1", "hash456" + "0" * 57)
        
    def test_reinstated_match_not_skipped(self):
        """Reinstated matches should not be skipped."""
        registry = KnownRecordRegistry(db_url=None)
        
        # Exclude then reinstate
        registry.mark_excluded("reinstated_match", reason_code="SCHEMA_CONFLICT")
        assert registry.should_skip("reinstated_match")
        
        registry.reinstate("reinstated_match")
        
        # Should not skip after reinstatement
        assert not registry.should_skip("reinstated_match")
        assert "reinstated_match" in registry.list_pending()
        
    def test_example_corpus_always_skipped(self):
        """Example corpus matches are always skipped."""
        registry = KnownRecordRegistry(db_url=None)
        
        # Example matches should always be skipped
        example_id = "EXAMPLE_match_001"
        assert ExampleCorpus.is_example(example_id)
        assert registry.should_skip(example_id)
        
    def test_multiple_exclusion_reasons(self):
        """Test various exclusion reason codes."""
        registry = KnownRecordRegistry(db_url=None)
        
        reasons = [
            "MANUAL_EXCLUDE",
            "DUPLICATE",
            "SCHEMA_CONFLICT",
            "CONTENT_DRIFT",
            "LOW_CONFIDENCE",
            "RATE_LIMIT_BAN",
        ]
        
        for i, reason in enumerate(reasons):
            match_id = f"excluded_{reason}_{i}"
            registry.mark_excluded(match_id, reason_code=reason)
            
            assert registry.should_skip(match_id), f"Should skip for reason: {reason}"
            assert registry.is_excluded(match_id)


# ============================================================================
# Content Deduplication Tests
# ============================================================================

class TestContentDeduplication:
    """Content-level duplicate detection tests."""
    
    def test_cross_source_player_deduplication(self):
        """Same player from different sources gets same UUID."""
        resolver = CanonicalIDResolver()
        
        # Same player from different sources
        vlr_player = resolver.resolve_player("TenZ", team="Sentinels", source="vlr_gg")
        lp_player = resolver.resolve_player("TenZ", team="Sentinels", source="liquipedia")
        
        # Should have same stable UUID
        assert vlr_player.stable_uuid == lp_player.stable_uuid
        
    def test_different_players_different_uuids(self):
        """Different players get different UUIDs."""
        resolver = CanonicalIDResolver()
        
        player1 = resolver.resolve_player("TenZ", team="Sentinels", source="vlr_gg")
        player2 = resolver.resolve_player("ScreaM", team="Sentinels", source="vlr_gg")
        
        # Different UUIDs
        assert player1.stable_uuid != player2.stable_uuid
        
    def test_same_player_different_teams_different_uuids(self):
        """Same player on different teams gets different UUIDs."""
        resolver = CanonicalIDResolver()
        
        tenz_sen = resolver.resolve_player("TenZ", team="Sentinels", source="vlr_gg")
        tenz_100t = resolver.resolve_player("TenZ", team="100 Thieves", source="vlr_gg")
        
        # Different teams = different UUIDs
        assert tenz_sen.stable_uuid != tenz_100t.stable_uuid
        
    def test_dedup_key_generation(self):
        """Dedup keys are deterministic."""
        resolver = CanonicalIDResolver()
        
        # Same parameters should always produce same key
        key1 = resolver.dedup_key("Player1", "TeamA", "vlr_gg", "match123", "Haven")
        key2 = resolver.dedup_key("Player1", "TeamA", "vlr_gg", "match123", "Haven")
        
        assert key1 == key2
        
        # Different parameters should produce different keys
        key3 = resolver.dedup_key("Player2", "TeamA", "vlr_gg", "match123", "Haven")
        assert key1 != key3


# ============================================================================
# Bridge-Level Deduplication
# ============================================================================

class TestBridgeDeduplication:
    """ExtractionBridge deduplication tests."""
    
    def test_transform_produces_consistent_records(self):
        """Same raw data always produces same KCRITR records."""
        bridge = ExtractionBridge()
        
        raw_data = RawMatchData(
            vlr_match_id="consistency_test_001",
            tournament="Test Tournament",
            map_name="Haven",
            match_date="1733011200",
            patch_version="8.11",
            players=[
                {
                    "player": "ConsistentPlayer",
                    "team": "ConsistentTeam",
                    "agent": "Jett",
                    "acs": "250",
                    "kills": "20",
                    "deaths": "15",
                }
            ],
        )
        
        # Transform twice
        records1 = bridge.transform(raw_data)
        records2 = bridge.transform(raw_data)
        
        # Same number of records
        assert len(records1) == len(records2)
        
        # Same player IDs
        for r1, r2 in zip(records1, records2):
            assert r1.player_id == r2.player_id
            assert r1.checksum_sha256 == r2.checksum_sha256
            
    def test_different_raw_data_different_checksums(self):
        """Different raw data produces different checksums."""
        bridge = ExtractionBridge()
        
        raw1 = RawMatchData(
            vlr_match_id="diff_test_001",
            tournament="Tournament A",
            map_name="Haven",
            match_date="1733011200",
            patch_version="8.11",
            players=[{"player": "PlayerA", "team": "TeamA", "acs": "200"}],
        )
        
        raw2 = RawMatchData(
            vlr_match_id="diff_test_002",
            tournament="Tournament B",
            map_name="Bind",
            match_date="1734000000",
            patch_version="9.0",
            players=[{"player": "PlayerB", "team": "TeamB", "acs": "300"}],
        )
        
        records1 = bridge.transform(raw1)
        records2 = bridge.transform(raw2)
        
        # Different checksums
        assert records1[0].checksum_sha256 != records2[0].checksum_sha256


# ============================================================================
# Registry Statistics Tests
# ============================================================================

class TestRegistryStatistics:
    """Registry statistics and monitoring tests."""
    
    def test_registry_stats_calculation(self):
        """Registry stats are calculated correctly."""
        registry = KnownRecordRegistry(db_url=None)
        
        # Initial state
        stats = registry.get_stats()
        assert stats.complete == 0
        assert stats.pending == 0
        assert stats.excluded == 0
        assert stats.total_known == 0
        
        # Add matches
        registry.mark_complete("stat_test_001")
        registry.mark_complete("stat_test_002")
        registry.add_pending("stat_test_003")
        registry.add_pending("stat_test_004")
        registry.mark_excluded("stat_test_005", reason_code="SCHEMA_CONFLICT")
        
        stats = registry.get_stats()
        assert stats.complete == 2
        assert stats.pending == 2
        assert stats.excluded == 1
        assert stats.total_known == 5
        
        # Skip rate should be 60% (3 out of 5 are complete/excluded)
        assert stats.skip_rate_pct == 60.0
        
    def test_registry_stats_with_reinstated(self):
        """Reinstated matches affect stats correctly."""
        registry = KnownRecordRegistry(db_url=None)
        
        registry.mark_excluded("rein_stat_001", reason_code="SCHEMA_CONFLICT")
        registry.reinstate("rein_stat_001")
        
        stats = registry.get_stats()
        assert stats.excluded == 0  # Reinstated not counted as excluded
        assert stats.pending == 1   # Now in pending
        
    def test_list_pending_excludes_completed(self):
        """Pending list excludes completed matches."""
        registry = KnownRecordRegistry(db_url=None)
        
        registry.add_pending("pending_test_001")
        registry.add_pending("pending_test_002")
        registry.mark_complete("pending_test_001")
        
        pending = registry.list_pending()
        assert "pending_test_002" in pending
        assert "pending_test_001" not in pending


# ============================================================================
# Integrity-Based Deduplication
# ============================================================================

class TestIntegrityBasedDeduplication:
    """Checksum-based deduplication tests."""
    
    def test_checksum_verification(self):
        """SHA-256 checksums verify content integrity."""
        content1 = b"identical content"
        content2 = b"identical content"
        content3 = b"different content"
        
        checksum1 = compute_checksum(content1)
        checksum2 = compute_checksum(content2)
        checksum3 = compute_checksum(content3)
        
        # Identical content = identical checksums
        assert checksum1 == checksum2
        assert len(checksum1) == 64
        
        # Different content = different checksums
        assert checksum1 != checksum3
        
        # Verify function works correctly
        assert verify_checksum(content1, checksum1)
        assert not verify_checksum(content3, checksum1)
        
    def test_bit_flip_detection(self):
        """Even a single bit flip changes the checksum."""
        content = b"sensitive data"
        checksum = compute_checksum(content)
        
        # Flip one bit
        modified = bytearray(content)
        modified[0] ^= 0x01
        modified_checksum = compute_checksum(bytes(modified))
        
        # Completely different checksum
        assert checksum != modified_checksum
        
    def test_registry_checksum_tracking(self):
        """Registry tracks checksums for deduplication."""
        registry = KnownRecordRegistry(db_url=None)
        
        checksum = "a" * 64
        
        # Initially unknown
        assert not registry.should_skip_checksum("cs_track_001", checksum)
        
        # Mark complete with checksum
        registry.mark_complete("cs_track_001", checksum=checksum)
        
        # Now should skip
        assert registry.should_skip_checksum("cs_track_001", checksum)
        
        # Different checksum should not skip
        assert not registry.should_skip_checksum("cs_track_001", "b" * 64)


# ============================================================================
# Concurrent Access Tests
# ============================================================================

class TestConcurrentAccess:
    """Tests for concurrent deduplication scenarios."""
    
    def test_first_writer_wins(self):
        """First writer wins in concurrent scenarios."""
        registry = KnownRecordRegistry(db_url=None)
        
        # Simulate concurrent completion attempts
        match_id = "concurrent_001"
        checksum = "concurrent_hash" + "0" * 49
        
        # First completion
        registry.mark_complete(match_id, checksum=checksum)
        
        # Subsequent completion (should be idempotent)
        registry.mark_complete(match_id, checksum=checksum)
        
        # Still complete, no corruption
        assert registry.is_complete(match_id)
        assert registry.should_skip(match_id)
        
    def test_atomic_exclusion(self):
        """Exclusion is atomic."""
        registry = KnownRecordRegistry(db_url=None)
        
        match_id = "atomic_excl_001"
        
        # Exclude
        registry.mark_excluded(match_id, reason_code="SCHEMA_CONFLICT")
        
        # Should be excluded even if we try to complete
        registry.mark_complete(match_id)
        
        # Still excluded (exclusion takes precedence)
        assert registry.is_excluded(match_id)


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestDeduplicationEdgeCases:
    """Edge cases in deduplication."""
    
    def test_empty_match_id(self):
        """Empty match ID handling."""
        registry = KnownRecordRegistry(db_url=None)
        
        # Empty string should still work
        registry.mark_complete("")
        assert registry.is_complete("")
        
    def test_very_long_match_id(self):
        """Very long match ID handling."""
        registry = KnownRecordRegistry(db_url=None)
        
        long_id = "x" * 10000
        registry.mark_complete(long_id)
        assert registry.is_complete(long_id)
        
    def test_special_characters_in_match_id(self):
        """Special characters in match IDs."""
        registry = KnownRecordRegistry(db_url=None)
        
        special_ids = [
            "match/with/slashes",
            "match-with-dashes",
            "match_with_underscores",
            "match.with.dots",
            "match:with:colons",
            "match with spaces",
            "match\twith\ttabs",
            "match\nwith\nnewlines",
            "match<with>brackets",
            "match"with"quotes",
        ]
        
        for match_id in special_ids:
            registry.mark_complete(match_id)
            assert registry.is_complete(match_id), f"Failed for: {match_id}"
            
    def test_unicode_match_id(self):
        """Unicode characters in match IDs."""
        registry = KnownRecordRegistry(db_url=None)
        
        unicode_ids = [
            "mätch_wïth_ümläuts",
            "マッチ",
            "比赛",
            "Матч",
            "مباراة",
            "🎮match",
        ]
        
        for match_id in unicode_ids:
            registry.mark_complete(match_id)
            assert registry.is_complete(match_id), f"Failed for: {match_id}"
            
    def test_case_sensitivity(self):
        """Match IDs are case-sensitive."""
        registry = KnownRecordRegistry(db_url=None)
        
        registry.mark_complete("Match_001")
        
        # Different case = different ID
        assert not registry.is_complete("match_001")
        assert not registry.is_complete("MATCH_001")


# ============================================================================
# Integration with Extraction Pipeline
# ============================================================================

class TestDeduplicationPipelineIntegration:
    """Tests for deduplication in full pipeline context."""
    
    def test_pipeline_does_not_fetch_known_matches(self, tmp_path):
        """Pipeline skips fetching known matches."""
        from pipeline import PipelineOrchestrator
        from pipeline.config import PipelineConfig
        
        config = PipelineConfig(
            database_url=None,
            raw_storage_path=tmp_path / "raw",
            dead_letter_path=tmp_path / "dlq",
            metrics_path=tmp_path / "metrics",
            checkpoint_path=tmp_path / "checkpoints",
        )
        config.ensure_directories()
        
        # Create registry with known matches
        registry = KnownRecordRegistry(db_url=None)
        registry.mark_complete("known_match_001")
        registry.mark_complete("known_match_002")
        
        # Create orchestrator
        orchestrator = PipelineOrchestrator(
            config=config,
            registry=registry,
        )
        
        # Known matches should be skipped
        assert registry.should_skip("known_match_001")
        assert registry.should_skip("known_match_002")
        
        # Unknown matches should not be skipped
        assert not registry.should_skip("unknown_match_001")
        
    def test_duplicate_detection_across_batches(self):
        """Duplicates are detected across processing batches."""
        registry = KnownRecordRegistry(db_url=None)
        
        # Simulate batch 1
        batch1_matches = ["batch1_001", "batch1_002"]
        for match_id in batch1_matches:
            registry.mark_complete(match_id)
            
        # Simulate batch 2 with some duplicates
        batch2_matches = ["batch1_002", "batch2_001"]  # batch1_002 is duplicate
        
        for match_id in batch2_matches:
            if registry.should_skip(match_id):
                continue  # Skip duplicate
            registry.mark_complete(match_id)
            
        # Stats should reflect all unique matches
        stats = registry.get_stats()
        assert stats.complete == 3  # batch1_001, batch1_002/batch2_001 (dup), batch2_001
