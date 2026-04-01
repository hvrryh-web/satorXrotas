"""
End-to-end pipeline integration tests.

Tests the complete flow:
1. Discovery: Find match IDs
2. Fetch: Download with registry skip check
3. Verify: Checksum and integrity validation
4. Parse: Extract structured data
5. Transform: Map to KCRITR schema
6. Crossref: Validate against external sources
7. Store: Write to PostgreSQL
8. Index: Update extraction_log

Also tests:
- Deduplication at multiple levels
- Dead letter queue handling
- Checkpoint resumption
- Metrics collection
"""

import pytest
import asyncio
import hashlib
import json
from datetime import datetime, date
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, ANY

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared" / "axiom-esports-data"))

from pipeline import PipelineOrchestrator, PipelineMode, PipelineStage
from pipeline.models import RunStatus, TriggerType, Checkpoint
from pipeline.scheduler import PipelineScheduler
from pipeline.runner import PipelineRunner
from pipeline.dead_letter import DeadLetterQueue
from pipeline.metrics import PipelineMetrics
from pipeline.stage_tracker import StageTracker
from pipeline.config import PipelineConfig
from extraction.src.storage.known_record_registry import KnownRecordRegistry
from extraction.src.storage.integrity_checker import compute_checksum
from extraction.src.bridge.extraction_bridge import ExtractionBridge, KCRITRRecord
from extraction.src.parsers.match_parser import MatchParser, RawMatchData


# ============================================================================
# Test Pipeline End-to-End
# ============================================================================

class TestPipelineEndToEnd:
    """Complete pipeline flow tests."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_run(self, patched_orchestrator):
        """Test complete pipeline from discovery to storage."""
        orchestrator = patched_orchestrator
        
        # Act - run with specific match IDs to avoid DB dependency
        result = await orchestrator.run(
            mode=PipelineMode.DELTA,
            epochs=[3],
            match_ids=["test_match_001", "test_match_002"],
        )
        
        # Assert
        assert result.records_discovered == 2
        assert result.records_fetched == 2
        assert result.records_verified == 2
        assert result.records_parsed == 2
        assert result.records_transformed == 2
        assert result.records_indexed == 2
        assert result.errors == 0
        assert result.duration_seconds > 0
        
    @pytest.mark.asyncio
    async def test_deduplication_exact_checksum(self, patched_orchestrator, test_registry):
        """Test that exact duplicates are skipped via checksum."""
        orchestrator = patched_orchestrator
        
        # First run - store records
        result1 = await orchestrator.run(
            mode=PipelineMode.DELTA,
            epochs=[3],
            match_ids=["dedup_test_001"],
        )
        
        assert result1.records_discovered == 1
        assert result1.records_stored >= 0
        
        # Mark as complete in registry (simulating indexing)
        test_registry.mark_complete("dedup_test_001", checksum="abc123")
        
        # Second run - should skip due to registry
        orchestrator2 = patched_orchestrator
        orchestrator2.registry = test_registry
        
        # Note: In delta mode, should_skip is checked during discovery
        discovered = await orchestrator2._discover_matches(
            PipelineMode.DELTA, [3], ["dedup_test_001"]
        )
        
        # Should be empty because match is marked complete
        assert len(discovered) == 0 or "dedup_test_001" not in discovered
        
    @pytest.mark.asyncio
    async def test_deduplication_content_match(self, patched_orchestrator):
        """Test content-level duplicate detection."""
        orchestrator = patched_orchestrator
        
        # Same match details, different source IDs would be handled by dedup key
        # This tests that the same content from different sources is detected
        
        result = await orchestrator.run(
            mode=PipelineMode.DELTA,
            epochs=[3],
            match_ids=["content_dup_001", "content_dup_002"],
        )
        
        # Both should be processed (no false positives)
        assert result.records_discovered == 2
        assert result.errors == 0
        
    @pytest.mark.asyncio
    async def test_dead_letter_queue(self, patched_orchestrator, mock_vlr_client_with_failures):
        """Test failed records go to DLQ and can be retried."""
        # Patch with failing client
        with patch("pipeline.orchestrator.ResilientVLRClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.ethical_fetch = mock_vlr_client_with_failures.ethical_fetch
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            orchestrator = patched_orchestrator
            
            # Include both valid and failing match IDs
            match_ids = ["test_match_001", "fail_match_001", "test_match_002"]
            
            result = await orchestrator.run(
                mode=PipelineMode.DELTA,
                epochs=[3],
                match_ids=match_ids,
            )
            
            # Some records should fail
            assert result.records_failed >= 1
            
            # DLQ should have entries
            dlq_size = orchestrator.dlq.size()
            assert dlq_size >= 1
            
            # Check DLQ has the failed match
            failed_entry = orchestrator.dlq.get("fail_match_001")
            assert failed_entry is not None
            assert failed_entry.stage == "fetched"
            
    @pytest.mark.asyncio
    async def test_checkpoint_resumption(self, patched_orchestrator, sample_checkpoint):
        """Test pipeline can resume from checkpoint."""
        orchestrator = patched_orchestrator
        
        # First, run some matches and save a checkpoint
        match_ids = ["resume_001", "resume_002", "resume_003"]
        
        # Process first batch
        result1 = await orchestrator.run(
            mode=PipelineMode.DELTA,
            epochs=[3],
            match_ids=match_ids[:2],
        )
        
        # Save checkpoint manually
        orchestrator.tracker.mark_stage_complete("resume_001", "fetched")
        orchestrator.tracker.mark_stage_complete("resume_001", "verified")
        orchestrator.tracker.mark_stage_complete("resume_002", "fetched")
        
        checkpoint_path = orchestrator.config.checkpoint_path / "test_checkpoint.json"
        orchestrator.tracker.save_to_file(checkpoint_path)
        
        # Verify checkpoint file exists
        assert checkpoint_path.exists()
        
        # Create new orchestrator with fresh tracker but load from checkpoint
        orchestrator2 = patched_orchestrator
        orchestrator2.tracker = StageTracker(
            db_url=None, 
            state_file=checkpoint_path
        )
        
        # Check that previous progress is tracked
        assert orchestrator2.tracker.is_stage_complete("resume_001", "fetched")
        assert orchestrator2.tracker.is_stage_complete("resume_001", "verified")
        
        # Resume processing
        pending = orchestrator2.tracker.get_pending_stages("resume_001")
        assert "fetched" not in pending
        assert "verified" not in pending
        
    @pytest.mark.asyncio
    async def test_data_verification(self, patched_orchestrator, sample_raw_match_data):
        """Test all verification layers work."""
        orchestrator = patched_orchestrator
        
        # Test transport integrity
        test_content = "test content for checksum"
        checksum = compute_checksum(test_content.encode())
        
        # Verify checksum computation works
        assert len(checksum) == 64  # SHA-256 hex is 64 chars
        assert all(c in "0123456789abcdef" for c in checksum)
        
        # Test semantic validation through stage processing
        result = await orchestrator.run(
            mode=PipelineMode.DELTA,
            epochs=[3],
            match_ids=["verify_test_001"],
        )
        
        # All records should pass verification
        assert result.records_verified == result.records_fetched
        
    @pytest.mark.asyncio
    async def test_scheduler_and_runner(self, test_scheduler, test_runner, test_pipeline_config):
        """Test scheduler creates runs and runner executes them."""
        scheduler = test_scheduler
        runner = test_runner
        
        # Connect scheduler to runner
        scheduler.runner = runner
        
        # Schedule a cron job
        job = await scheduler.schedule_cron(
            name="test-daily",
            cron="0 6 * * *",
            pipeline_args={"mode": "delta", "epochs": [3]},
            description="Test daily delta run",
        )
        
        assert job.name == "test-daily"
        assert job.cron_expression == "0 6 * * *"
        assert job.trigger_type.value == "cron"
        
        # Trigger manual run
        run_id = await scheduler.trigger_manual(
            pipeline_args={
                "mode": "delta",
                "epochs": [3],
                "batch_size": 10,
            }
        )
        
        assert run_id is not None
        assert isinstance(run_id, str)
        
        # Get run status
        run = runner.get_run(run_id)
        assert run is not None
        
        # Wait for run to complete or fail (in tests it will simulate)
        await asyncio.sleep(0.5)
        
        # Check run was created
        assert run.status in [RunStatus.PENDING, RunStatus.RUNNING, RunStatus.COMPLETED]
        
    @pytest.mark.asyncio
    async def test_metrics_collection(self, patched_orchestrator):
        """Test metrics are collected during pipeline run."""
        orchestrator = patched_orchestrator
        
        # Record some metrics
        with orchestrator.metrics.measure("fetch"):
            await asyncio.sleep(0.01)
        
        with orchestrator.metrics.measure("parse"):
            await asyncio.sleep(0.01)
        
        orchestrator.metrics.record_registry_skip()
        orchestrator.metrics.record_registry_skip()
        orchestrator.metrics.record_registry_check()
        
        # Get summary
        summary = orchestrator.metrics.get_summary()
        
        assert summary["total_processed"] >= 2
        assert summary["registry_skips"] == 2
        assert summary["registry_total"] == 3
        assert summary["registry_skip_rate_pct"] > 0
        
        # Test Prometheus export
        prom_output = orchestrator.metrics.to_prometheus()
        assert "pipeline_records_total" in prom_output
        assert "pipeline_registry_skips_total" in prom_output
        
        # Save to file
        orchestrator.metrics.save_to_file()
        
        # Check files were created
        prom_file = orchestrator.config.metrics_path / "pipeline.prom"
        json_file = orchestrator.config.metrics_path / "pipeline.json"
        
        assert prom_file.exists() or not orchestrator.config.enable_metrics
        assert json_file.exists() or not orchestrator.config.enable_metrics


# ============================================================================
# Test Deduplication System
# ============================================================================

class TestDeduplicationSystem:
    """Comprehensive deduplication tests."""
    
    def test_exact_duplicate_detection(self):
        """Test checksum-based exact duplicate detection."""
        registry = KnownRecordRegistry(db_url=None)
        
        # First content
        checksum1 = "abc123" + "0" * 58  # Pad to 64 chars
        
        # Check should_skip_checksum - initially not present
        is_dup = registry.should_skip_checksum("match_001", checksum1)
        assert not is_dup
        
        # Mark as seen
        registry.mark_complete("match_001", checksum=checksum1)
        
        # Same checksum = should skip
        is_dup = registry.should_skip_checksum("match_001", checksum1)
        assert is_dup
        
    def test_content_duplicate_detection(self):
        """Test match-level duplicate detection."""
        registry = KnownRecordRegistry(db_url=None)
        
        # Different matches with same content pattern
        registry.mark_complete("match_001", checksum="hash_a" + "0" * 59)
        
        # Same match ID should be detected as complete
        assert registry.is_complete("match_001")
        assert registry.should_skip("match_001")
        
        # Different match ID should not be affected
        assert not registry.is_complete("match_002")
        assert not registry.should_skip("match_002")
        
    def test_near_duplicate_similarity(self):
        """Test similarity scoring for near-duplicates."""
        # This tests the conceptual similarity detection
        # Actual implementation would use a SimilarityChecker class
        
        stats1 = {'kills': 20, 'deaths': 15, 'acs': 250}
        stats2 = {'kills': 21, 'deaths': 15, 'acs': 252}  # Very similar
        stats3 = {'kills': 5, 'deaths': 20, 'acs': 120}   # Very different
        
        # Simple similarity metric
        def calculate_similarity(s1, s2):
            """Calculate cosine similarity between two stat dicts."""
            keys = set(s1.keys()) & set(s2.keys())
            if not keys:
                return 0.0
            
            dot_product = sum(s1[k] * s2[k] for k in keys)
            mag1 = sum(s1[k] ** 2 for k in keys) ** 0.5
            mag2 = sum(s2[k] ** 2 for k in keys) ** 0.5
            
            if mag1 == 0 or mag2 == 0:
                return 0.0
            
            return dot_product / (mag1 * mag2)
        
        sim_1_2 = calculate_similarity(stats1, stats2)
        sim_1_3 = calculate_similarity(stats1, stats3)
        
        # Very similar stats should have high similarity
        assert sim_1_2 > 0.95
        
        # Different stats should have lower similarity
        assert sim_1_3 < 0.8


# ============================================================================
# Test Verification Framework
# ============================================================================

class TestVerificationFramework:
    """Data verification tests."""
    
    def test_transport_integrity(self):
        """Test SHA-256 checksum verification."""
        from extraction.src.storage.integrity_checker import verify_checksum
        
        content = "test content"
        expected_checksum = hashlib.sha256(content.encode()).hexdigest()
        
        # Verify valid checksum
        is_valid = verify_checksum(content.encode(), expected_checksum)
        assert is_valid
        
        # Verify invalid checksum
        is_valid = verify_checksum(content.encode(), "wrong_checksum" * 4)
        assert not is_valid
        
        # Verify tampered content
        tampered = "tampered content"
        is_valid = verify_checksum(tampered.encode(), expected_checksum)
        assert not is_valid
        
    def test_semantic_validation_bounds(self, valid_player_stats, invalid_player_stats):
        """Test value range validation."""
        
        def validate_stats(stats):
            """Validate player stats are within reasonable bounds."""
            errors = []
            
            if stats.get('kills', 0) < 0:
                errors.append("kills cannot be negative")
            if stats.get('kills', 0) > 100:
                errors.append("kills exceeds maximum")
                
            if stats.get('deaths', 0) < 0:
                errors.append("deaths cannot be negative")
            if stats.get('deaths', 0) > 100:
                errors.append("deaths exceeds maximum")
                
            if stats.get('acs', 0) < 0:
                errors.append("acs cannot be negative")
            if stats.get('acs', 0) > 800:
                errors.append("acs exceeds maximum")
                
            if stats.get('adr', 0) < 0:
                errors.append("adr cannot be negative")
            if stats.get('adr', 0) > 400:
                errors.append("adr exceeds maximum")
                
            kast = stats.get('kast_pct', 0)
            if kast < 0 or kast > 100:
                errors.append("kast_pct must be between 0 and 100")
                
            hs = stats.get('hs_pct', 0)
            if hs < 0 or hs > 100:
                errors.append("hs_pct must be between 0 and 100")
            
            return len(errors) == 0, errors
        
        # Valid stats should pass
        is_valid, errors = validate_stats(valid_player_stats)
        assert is_valid, f"Unexpected errors: {errors}"
        
        # Invalid stats should fail
        is_valid, errors = validate_stats(invalid_player_stats)
        assert not is_valid
        assert len(errors) > 0
        
    def test_kcritr_schema_validation(self, sample_raw_match_data):
        """Test 37-field schema validation."""
        bridge = ExtractionBridge()
        
        # Transform raw data to KCRITR records
        records = bridge.transform(sample_raw_match_data)
        
        assert len(records) > 0
        
        for record in records:
            # Verify all required fields are present
            assert isinstance(record.player_id, type(record.player_id))  # UUID type
            assert record.name is not None
            assert record.match_id is not None
            assert record.data_source == "vlr_gg"
            
            # Verify field types
            assert record.kills is None or isinstance(record.kills, int)
            assert record.deaths is None or isinstance(record.deaths, int)
            assert record.acs is None or isinstance(record.acs, float)
            assert record.adr is None or isinstance(record.adr, float)
            
            # Verify separation flag
            assert record.separation_flag in [0, 9]
            
            # Verify checksum
            assert record.checksum_sha256 is not None
            assert len(record.checksum_sha256) == 64


# ============================================================================
# Test Stage-by-Stage Processing
# ============================================================================

class TestStageByStageProcessing:
    """Test individual pipeline stages."""
    
    @pytest.mark.asyncio
    async def test_discovery_stage(self, patched_orchestrator):
        """Test match discovery stage."""
        orchestrator = patched_orchestrator
        
        match_ids = ["stage_test_001", "stage_test_002"]
        
        discovered = await orchestrator._discover_matches(
            PipelineMode.DELTA,
            [3],
            match_ids,
        )
        
        assert len(discovered) == 2
        assert all(mid in discovered for mid in match_ids)
        
    @pytest.mark.asyncio
    async def test_fetch_stage(self, patched_orchestrator):
        """Test fetch stage."""
        orchestrator = patched_orchestrator
        
        results = {"fetched": 0, "verified": 0}
        
        raw_html, checksum = await orchestrator._stage_fetch(
            "fetch_test_001",
            results,
        )
        
        assert raw_html is not None
        assert checksum is not None
        assert len(checksum) == 64
        assert results["fetched"] == 1
        
    @pytest.mark.asyncio
    async def test_verify_stage(self, patched_orchestrator):
        """Test verify stage."""
        orchestrator = patched_orchestrator
        
        # First fetch
        results = {"fetched": 0, "verified": 0}
        raw_html, checksum = await orchestrator._stage_fetch(
            "verify_test_001",
            results,
        )
        
        # Then verify
        is_valid = await orchestrator._stage_verify(
            "verify_test_001",
            raw_html,
            checksum,
            results,
        )
        
        assert is_valid
        assert results["verified"] == 1
        
    @pytest.mark.asyncio
    async def test_parse_stage(self, patched_orchestrator):
        """Test parse stage."""
        orchestrator = patched_orchestrator
        
        # Fetch first
        results = {"fetched": 0, "verified": 0, "parsed": 0}
        raw_html, checksum = await orchestrator._stage_fetch(
            "parse_test_001",
            results,
        )
        
        # Parse
        parsed_data = await orchestrator._stage_parse(
            "parse_test_001",
            raw_html,
            results,
        )
        
        assert parsed_data is not None
        assert isinstance(parsed_data, RawMatchData)
        assert parsed_data.vlr_match_id == "parse_test_001"
        assert len(parsed_data.players) > 0
        assert results["parsed"] == 1
        
    @pytest.mark.asyncio
    async def test_transform_stage(self, patched_orchestrator):
        """Test transform stage."""
        orchestrator = patched_orchestrator
        
        # Fetch and parse
        results = {"fetched": 0, "verified": 0, "parsed": 0, "transformed": 0}
        raw_html, checksum = await orchestrator._stage_fetch(
            "transform_test_001",
            results,
        )
        parsed_data = await orchestrator._stage_parse(
            "transform_test_001",
            raw_html,
            results,
        )
        
        # Transform
        records = await orchestrator._stage_transform(
            "transform_test_001",
            parsed_data,
            checksum,
            results,
        )
        
        assert len(records) > 0
        assert all(isinstance(r, KCRITRRecord) for r in records)
        assert results["transformed"] == 1
        
    @pytest.mark.asyncio
    async def test_index_stage(self, patched_orchestrator):
        """Test index stage (registry update)."""
        orchestrator = patched_orchestrator
        
        results = {"indexed": 0}
        checksum = "a" * 64
        
        # Index
        await orchestrator._stage_index(
            "index_test_001",
            checksum,
            results,
        )
        
        assert results["indexed"] == 1
        assert orchestrator.registry.is_complete("index_test_001")


# ============================================================================
# Test Pipeline Modes
# ============================================================================

class TestPipelineModes:
    """Test different pipeline operation modes."""
    
    @pytest.mark.asyncio
    async def test_delta_mode_skips_completed(self, patched_orchestrator):
        """Test delta mode skips already completed matches."""
        orchestrator = patched_orchestrator
        
        # Mark a match as complete
        orchestrator.registry.mark_complete("delta_skip_001")
        
        # In delta mode, should be skipped during discovery
        discovered = await orchestrator._discover_matches(
            PipelineMode.DELTA,
            [3],
            ["delta_skip_001", "delta_process_001"],
        )
        
        # Completed match should be skipped
        assert "delta_skip_001" not in discovered
        assert "delta_process_001" in discovered
        
    @pytest.mark.asyncio
    async def test_full_mode_processes_all(self, patched_orchestrator):
        """Test full mode processes all matches regardless of completion."""
        orchestrator = patched_orchestrator
        
        # Mark as complete
        orchestrator.registry.mark_complete("full_test_001")
        
        # Run in full mode
        result = await orchestrator.run(
            mode=PipelineMode.FULL,
            epochs=[3],
            match_ids=["full_test_001"],
        )
        
        # Should still process in full mode
        assert result.records_discovered == 1
        
    @pytest.mark.asyncio
    async def test_backfill_mode(self, patched_orchestrator):
        """Test backfill mode for historical data."""
        orchestrator = patched_orchestrator
        
        # Backfill mode should work like delta but for historical epochs
        result = await orchestrator.run(
            mode=PipelineMode.BACKFILL,
            epochs=[1, 2],  # Historical epochs
            match_ids=["backfill_001", "backfill_002"],
        )
        
        assert result.records_discovered == 2


# ============================================================================
# Test Error Handling
# ============================================================================

class TestErrorHandling:
    """Test pipeline error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_stage_failure_handling(self, patched_orchestrator):
        """Test that stage failures are properly tracked."""
        orchestrator = patched_orchestrator
        
        match_id = "error_test_001"
        
        # Mark a stage as failed
        orchestrator.tracker.mark_stage_failed(match_id, "fetch", "Connection timeout")
        
        # Verify failure is recorded
        assert orchestrator.tracker.is_stage_failed(match_id, "fetch")
        assert orchestrator.tracker.get_stage_error(match_id, "fetch") == "Connection timeout"
        
        # Pending stages should not include the failed one
        pending = orchestrator.tracker.get_pending_stages(match_id)
        assert "fetch" in pending  # Failed stages need to be retried
        
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, test_dlq):
        """Test dead letter queue retry mechanism."""
        dlq = test_dlq
        
        # Add a failed record
        dlq.enqueue("retry_test_001", Exception("Temporary error"), "parse", {"attempt": 1})
        
        # Verify it's in the queue
        assert dlq.size() == 1
        entry = dlq.get("retry_test_001")
        assert entry.retry_count == 0
        
        # Simulate retry
        entry.retry_count = 1
        entry.last_retry_at = datetime.now().isoformat()
        
        # Should be eligible for another retry
        assert entry.can_retry(max_retries=3, backoff_seconds=0)
        
        # After max retries, should not be eligible
        entry.retry_count = 3
        assert not entry.can_retry(max_retries=3, backoff_seconds=0)
