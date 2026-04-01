"""
Tests for the pipeline orchestrator.

Run with: pytest pipeline/tests/test_orchestrator.py -v
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import pytest

# Import after path setup
from pipeline.orchestrator import (
    PipelineOrchestrator,
    PipelineMode,
    PipelineStage,
    PipelineResult,
    parse_stage,
    parse_epochs,
)
from pipeline.config import PipelineConfig
from pipeline.stage_tracker import StageTracker, StageState
from pipeline.metrics import PipelineMetrics
from pipeline.dead_letter import DeadLetterQueue, DeadLetterEntry


class TestPipelineConfig:
    """Test configuration management."""
    
    def test_default_config(self):
        config = PipelineConfig()
        assert config.mode == "delta"
        assert config.epochs == [1, 2, 3]
        assert config.batch_size == 100
        assert config.max_workers == 3
    
    def test_config_validation_valid(self):
        config = PipelineConfig(mode="full", epochs=[2, 3])
        config.validate()  # Should not raise
    
    def test_config_validation_invalid_mode(self):
        config = PipelineConfig(mode="invalid")
        with pytest.raises(ValueError, match="Invalid mode"):
            config.validate()
    
    def test_config_validation_invalid_epochs(self):
        config = PipelineConfig(epochs=[1, 4, 5])
        with pytest.raises(ValueError, match="Invalid epochs"):
            config.validate()
    
    def test_ensure_directories(self, tmp_path):
        config = PipelineConfig()
        config.dead_letter_path = tmp_path / "dlq"
        config.metrics_path = tmp_path / "metrics"
        config.checkpoint_path = tmp_path / "checkpoints"
        config.ensure_directories()
        
        assert config.dead_letter_path.exists()
        assert config.metrics_path.exists()
        assert config.checkpoint_path.exists()


class TestStageTracker:
    """Test stage tracking functionality."""
    
    def test_get_pending_stages_empty(self):
        tracker = StageTracker()
        pending = tracker.get_pending_stages("match_123")
        assert pending == StageTracker.STAGES
    
    def test_mark_stage_complete(self):
        tracker = StageTracker()
        tracker.mark_stage_complete("match_123", "fetched")
        
        assert tracker.is_stage_complete("match_123", "fetched")
        pending = tracker.get_pending_stages("match_123")
        assert "fetched" not in pending
    
    def test_mark_stage_failed(self):
        tracker = StageTracker()
        tracker.mark_stage_failed("match_123", "fetch", "Connection timeout")
        
        assert tracker.is_stage_failed("match_123", "fetch")
        assert tracker.get_stage_error("match_123", "fetch") == "Connection timeout"
    
    def test_is_complete(self):
        tracker = StageTracker()
        
        # Initially not complete
        assert not tracker.is_complete("match_123")
        
        # Mark all stages complete
        for stage in StageTracker.STAGES:
            tracker.mark_stage_complete("match_123", stage)
        
        assert tracker.is_complete("match_123")
    
    def test_reset_match(self):
        tracker = StageTracker()
        tracker.mark_stage_complete("match_123", "fetched")
        tracker.mark_stage_complete("match_123", "parsed")
        
        tracker.reset_match("match_123")
        
        pending = tracker.get_pending_stages("match_123")
        assert "fetched" in pending
        assert "parsed" in pending
    
    def test_get_stats(self):
        tracker = StageTracker()
        tracker.mark_stage_complete("match_1", "fetched")
        tracker.mark_stage_complete("match_1", "parsed")
        tracker.mark_stage_complete("match_2", "fetched")
        
        stats = tracker.get_stats()
        assert stats["total_matches"] == 2
        assert stats["stage_completion"]["fetched"] == 2
        assert stats["stage_completion"]["parsed"] == 1
    
    def test_save_and_load(self, tmp_path):
        tracker = StageTracker(state_file=tmp_path / "state.json")
        tracker.mark_stage_complete("match_123", "fetched")
        tracker.mark_stage_failed("match_456", "parse", "Error")
        tracker.save_to_file()
        
        # Load into new tracker
        tracker2 = StageTracker(state_file=tmp_path / "state.json")
        assert tracker2.is_stage_complete("match_123", "fetched")
        assert tracker2.is_stage_failed("match_456", "parse")


class TestPipelineMetrics:
    """Test metrics collection."""
    
    def test_record_success(self):
        metrics = PipelineMetrics()
        metrics.record_success("fetch", 1.5)
        
        stats = metrics.get_stage_stats("fetch")
        assert stats.records_processed == 1
        assert stats.total_duration_seconds == 1.5
    
    def test_record_failure(self):
        metrics = PipelineMetrics()
        metrics.record_failure("fetch", "ConnectionError", 2.0)
        
        stats = metrics.get_stage_stats("fetch")
        assert stats.records_failed == 1
        assert stats.errors_by_type["ConnectionError"] == 1
    
    def test_measure_context_manager(self):
        metrics = PipelineMetrics()
        
        with metrics.measure("fetch"):
            pass  # Simulate work
        
        stats = metrics.get_stage_stats("fetch")
        assert stats.records_processed == 1
    
    def test_measure_context_manager_exception(self):
        metrics = PipelineMetrics()
        
        try:
            with metrics.measure("fetch"):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        stats = metrics.get_stage_stats("fetch")
        assert stats.records_failed == 1
        assert stats.errors_by_type["ValueError"] == 1
    
    def test_registry_skip_rate(self):
        metrics = PipelineMetrics()
        
        # 3 checks, 2 skips = 66.67% skip rate
        metrics.record_registry_check()
        metrics.record_registry_skip()
        metrics.record_registry_check()
        metrics.record_registry_skip()
        
        assert abs(metrics.get_registry_skip_rate() - 66.67) < 0.1
    
    def test_to_prometheus_format(self):
        metrics = PipelineMetrics()
        metrics.record_success("fetch", 1.0)
        metrics.record_success("parse", 0.5)
        metrics.set_active_workers(3)
        
        output = metrics.to_prometheus()
        
        assert "pipeline_records_total" in output
        assert 'stage="fetch"' in output
        assert "pipeline_active_workers 3" in output
    
    def test_to_json(self):
        metrics = PipelineMetrics()
        metrics.record_success("fetch", 1.0)
        
        output = metrics.to_json()
        data = json.loads(output)
        
        assert data["total_processed"] == 1
        assert "stage_stats" in data


class TestDeadLetterQueue:
    """Test dead letter queue functionality."""
    
    def test_enqueue(self):
        dlq = DeadLetterQueue()
        error = ValueError("Test error")
        
        dlq.enqueue("match_123", error, "fetch", {"url": "http://test"})
        
        assert dlq.size() == 1
        entry = dlq.get("match_123")
        assert entry.match_id == "match_123"
        assert entry.error_type == "ValueError"
        assert entry.stage == "fetch"
    
    def test_dequeue(self):
        dlq = DeadLetterQueue()
        dlq.enqueue("match_123", ValueError("Test"), "fetch", {})
        
        entry = dlq.dequeue("match_123")
        assert entry is not None
        assert dlq.size() == 0
    
    def test_list_pending(self):
        dlq = DeadLetterQueue()
        dlq.enqueue("match_1", ValueError("Test"), "fetch", {})
        dlq.enqueue("match_2", ValueError("Test"), "parse", {})
        
        pending = dlq.list_pending(max_retries=3)
        assert "match_1" in pending
        assert "match_2" in pending
    
    def test_retry_all_success(self):
        dlq = DeadLetterQueue()
        dlq.enqueue("match_123", ValueError("Test"), "fetch", {})
        
        def processor(match_id, payload):
            return True
        
        results = dlq.retry_all(processor=processor, max_retries=3)
        
        assert results["success"] == 1
        assert results["failed"] == 0
        assert dlq.size() == 0  # Succeeded entries removed
    
    def test_retry_all_failure(self):
        dlq = DeadLetterQueue()
        dlq.enqueue("match_123", ValueError("Test"), "fetch", {})
        
        def processor(match_id, payload):
            raise RuntimeError("Still failing")
        
        results = dlq.retry_all(processor=processor, max_retries=1)
        
        assert results["success"] == 0
        assert results["failed"] == 1
        # Entry should still be in queue
        assert dlq.size() == 1
    
    def test_max_retries_exceeded(self):
        dlq = DeadLetterQueue()
        dlq.enqueue("match_123", ValueError("Test"), "fetch", {})
        
        # Simulate 3 failed retries
        entry = dlq.get("match_123")
        entry.retry_count = 3
        entry.status = "failed"
        
        pending = dlq.list_pending(max_retries=3)
        assert "match_123" not in pending
        
        failed = dlq.list_permanently_failed(max_retries=3)
        assert "match_123" in failed
    
    def test_save_and_load(self, tmp_path):
        dlq = DeadLetterQueue(storage_path=tmp_path)
        dlq.enqueue("match_123", ValueError("Test"), "fetch", {})
        
        # Create new DLQ pointing to same path
        dlq2 = DeadLetterQueue(storage_path=tmp_path)
        assert dlq2.size() == 1
        assert dlq2.get("match_123") is not None


class TestPipelineResult:
    """Test result data class."""
    
    def test_to_dict(self):
        result = PipelineResult(
            mode="delta",
            epochs=[1, 2],
            records_discovered=100,
            records_stored=95,
            records_failed=5,
            duration_seconds=120.5,
        )
        
        data = result.to_dict()
        assert data["mode"] == "delta"
        assert data["epochs"] == [1, 2]
        assert data["records_stored"] == 95
        assert data["duration_seconds"] == 120.5


class TestArgumentParsing:
    """Test CLI argument parsing."""
    
    def test_parse_stage_valid(self):
        assert parse_stage("fetch") == PipelineStage.FETCH
        assert parse_stage("FETCH") == PipelineStage.FETCH
        assert parse_stage("all") == PipelineStage.ALL
    
    def test_parse_stage_invalid(self):
        with pytest.raises(SystemExit):
            parse_stage("invalid")
    
    def test_parse_epochs_valid(self):
        assert parse_epochs("1,2,3") == [1, 2, 3]
        assert parse_epochs("2") == [2]
    
    def test_parse_epochs_invalid(self):
        with pytest.raises(SystemExit):
            parse_epochs("a,b,c")


class TestOrchestratorIntegration:
    """Integration tests for the orchestrator."""
    
    @pytest.fixture
    def temp_config(self, tmp_path):
        config = PipelineConfig()
        config.dead_letter_path = tmp_path / "dlq"
        config.metrics_path = tmp_path / "metrics"
        config.checkpoint_path = tmp_path / "checkpoints"
        config.batch_size = 10
        config.max_workers = 2
        config.ensure_directories()
        return config
    
    def test_orchestrator_initialization(self, temp_config):
        orchestrator = PipelineOrchestrator(config=temp_config)
        
        assert orchestrator.config == temp_config
        assert orchestrator.registry is not None
        assert orchestrator.tracker is not None
        assert orchestrator.metrics is not None
        assert orchestrator.dlq is not None
    
    def test_get_stages_to_run_all(self, temp_config):
        orchestrator = PipelineOrchestrator(config=temp_config)
        stages = orchestrator._get_stages_to_run(PipelineStage.ALL)
        assert stages == StageTracker.STAGES
    
    def test_get_stages_to_run_from_fetch(self, temp_config):
        orchestrator = PipelineOrchestrator(config=temp_config)
        stages = orchestrator._get_stages_to_run(PipelineStage.FETCH)
        assert stages == ["fetched"]
    
    def test_get_stages_to_run_from_transform(self, temp_config):
        orchestrator = PipelineOrchestrator(config=temp_config)
        stages = orchestrator._get_stages_to_run(PipelineStage.TRANSFORM)
        assert "fetched" in stages
        assert "verified" in stages
        assert "parsed" in stages
        assert "transformed" in stages


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
