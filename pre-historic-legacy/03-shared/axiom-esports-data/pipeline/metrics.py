"""
Pipeline Metrics Exporter
=========================

Prometheus-compatible metrics for monitoring pipeline health and performance.

Metrics exposed:
    - pipeline_records_total: Records processed per stage
    - pipeline_duration_seconds: Processing duration per stage
    - pipeline_errors_total: Error counts by type
    - pipeline_registry_skips_total: Registry skip rate
    - pipeline_active_workers: Current worker count
    - pipeline_dead_letter_size: Pending dead letter queue size

Example Prometheus scrape output:
    # HELP pipeline_records_total Total records processed
    # TYPE pipeline_records_total counter
    pipeline_records_total{stage="fetch"} 1250
    pipeline_records_total{stage="parse"} 1234
    
    # HELP pipeline_duration_seconds Processing duration
    # TYPE pipeline_duration_seconds histogram
    pipeline_duration_seconds_bucket{stage="fetch",le="1.0"} 950
    pipeline_duration_seconds_bucket{stage="fetch",le="2.0"} 1200
"""

import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class StageMetrics:
    """Metrics for a single pipeline stage."""
    records_processed: int = 0
    records_failed: int = 0
    total_duration_seconds: float = 0.0
    durations: list[float] = field(default_factory=list)
    errors_by_type: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    def record_success(self, duration_seconds: float) -> None:
        """Record a successful processing."""
        self.records_processed += 1
        self.total_duration_seconds += duration_seconds
        self.durations.append(duration_seconds)
        # Keep only last 1000 durations for memory efficiency
        if len(self.durations) > 1000:
            self.durations = self.durations[-1000:]
    
    def record_failure(self, duration_seconds: float, error_type: str) -> None:
        """Record a failed processing."""
        self.records_failed += 1
        self.total_duration_seconds += duration_seconds
        self.errors_by_type[error_type] += 1
    
    def get_avg_duration(self) -> float:
        """Get average processing duration."""
        total = self.records_processed + self.records_failed
        if total == 0:
            return 0.0
        return self.total_duration_seconds / total
    
    def get_p95_duration(self) -> float:
        """Get 95th percentile duration."""
        if not self.durations:
            return 0.0
        sorted_durations = sorted(self.durations)
        idx = int(len(sorted_durations) * 0.95)
        return sorted_durations[min(idx, len(sorted_durations) - 1)]


class PipelineMetrics:
    """Prometheus-compatible metrics exporter for pipeline monitoring.
    
    Tracks processing statistics and exports in Prometheus format.
    Also supports JSON export for alternative monitoring systems.
    
    Example:
        metrics = PipelineMetrics()
        
        # Record processing
        with metrics.measure("fetch"):
            result = fetch_data()
        
        # Or manual recording
        metrics.record_success("parse", duration=0.5)
        metrics.record_failure("store", error_type="ConnectionError")
        
        # Export metrics
        print(metrics.to_prometheus())
        metrics.save_to_file("/var/lib/metrics/pipeline.prom")
    """
    
    BUCKETS = [0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
    
    def __init__(self, metrics_path: Optional[Path] = None) -> None:
        """Initialize metrics collector.
        
        Args:
            metrics_path: Directory to save metrics files
        """
        self.metrics_path = metrics_path
        self._stage_metrics: dict[str, StageMetrics] = defaultdict(StageMetrics)
        self._registry_skips: int = 0
        self._registry_total: int = 0
        self._active_workers: int = 0
        self._dead_letter_size: int = 0
        self._start_time: float = time.time()
        self._checkpoints_saved: int = 0
        self._last_checkpoint_time: Optional[float] = None
        
        if self.metrics_path:
            self.metrics_path.mkdir(parents=True, exist_ok=True)
    
    # ------------------------------------------------------------------
    # Recording methods
    # ------------------------------------------------------------------
    
    def measure(self, stage: str):
        """Context manager for measuring stage duration.
        
        Args:
            stage: Name of the pipeline stage
            
        Example:
            with metrics.measure("fetch"):
                data = fetch_from_source()
        """
        return _MetricsTimer(self, stage)
    
    def record_success(self, stage: str, duration_seconds: float) -> None:
        """Record a successful stage completion.
        
        Args:
            stage: Name of the pipeline stage
            duration_seconds: Time taken to process
        """
        self._stage_metrics[stage].record_success(duration_seconds)
        logger.debug("Stage %s succeeded in %.3fs", stage, duration_seconds)
    
    def record_failure(
        self,
        stage: str,
        error_type: str,
        duration_seconds: float = 0.0,
    ) -> None:
        """Record a stage failure.
        
        Args:
            stage: Name of the pipeline stage
            error_type: Type/class name of the error
            duration_seconds: Time taken before failure
        """
        self._stage_metrics[stage].record_failure(duration_seconds, error_type)
        logger.warning("Stage %s failed (%s) in %.3fs", stage, error_type, duration_seconds)
    
    def record_registry_skip(self) -> None:
        """Record that a record was skipped by the registry."""
        self._registry_skips += 1
        self._registry_total += 1
    
    def record_registry_check(self) -> None:
        """Record that a registry check was performed (not skipped)."""
        self._registry_total += 1
    
    def set_active_workers(self, count: int) -> None:
        """Update the active worker count gauge."""
        self._active_workers = count
    
    def set_dead_letter_size(self, size: int) -> None:
        """Update the dead letter queue size gauge."""
        self._dead_letter_size = size
    
    def record_checkpoint(self) -> None:
        """Record that a checkpoint was saved."""
        self._checkpoints_saved += 1
        self._last_checkpoint_time = time.time()
    
    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------
    
    def get_stage_stats(self, stage: str) -> StageMetrics:
        """Get metrics for a specific stage."""
        return self._stage_metrics[stage]
    
    def get_total_processed(self) -> int:
        """Get total records processed across all stages."""
        return sum(m.records_processed for m in self._stage_metrics.values())
    
    def get_total_failed(self) -> int:
        """Get total records failed across all stages."""
        return sum(m.records_failed for m in self._stage_metrics.values())
    
    def get_registry_skip_rate(self) -> float:
        """Get registry skip rate as percentage."""
        if self._registry_total == 0:
            return 0.0
        return 100.0 * self._registry_skips / self._registry_total
    
    def get_summary(self) -> dict:
        """Get summary statistics as dictionary."""
        total_processed = self.get_total_processed()
        total_failed = self.get_total_failed()
        total_attempts = total_processed + total_failed
        
        uptime_seconds = time.time() - self._start_time
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": round(uptime_seconds, 2),
            "total_processed": total_processed,
            "total_failed": total_failed,
            "success_rate_pct": round(100 * total_processed / max(total_attempts, 1), 2),
            "registry_skip_rate_pct": round(self.get_registry_skip_rate(), 2),
            "registry_skips": self._registry_skips,
            "registry_total": self._registry_total,
            "active_workers": self._active_workers,
            "dead_letter_size": self._dead_letter_size,
            "checkpoints_saved": self._checkpoints_saved,
            "stage_stats": {
                stage: {
                    "processed": m.records_processed,
                    "failed": m.records_failed,
                    "avg_duration_seconds": round(m.get_avg_duration(), 3),
                    "p95_duration_seconds": round(m.get_p95_duration(), 3),
                    "errors_by_type": dict(m.errors_by_type),
                }
                for stage, m in self._stage_metrics.items()
            },
        }
    
    # ------------------------------------------------------------------
    # Export methods
    # ------------------------------------------------------------------
    
    def to_prometheus(self) -> str:
        """Export metrics in Prometheus exposition format.
        
        Returns:
            Multi-line string in Prometheus format
        """
        lines = []
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Records processed counter
        lines.append("# HELP pipeline_records_total Total records processed")
        lines.append("# TYPE pipeline_records_total counter")
        for stage, metrics in self._stage_metrics.items():
            lines.append(f'pipeline_records_total{{stage="{stage}"}} {metrics.records_processed}')
        
        # Records failed counter
        lines.append("# HELP pipeline_records_failed Total records failed")
        lines.append("# TYPE pipeline_records_failed counter")
        for stage, metrics in self._stage_metrics.items():
            lines.append(f'pipeline_records_failed{{stage="{stage}"}} {metrics.records_failed}')
        
        # Duration histogram (simplified)
        lines.append("# HELP pipeline_duration_seconds Processing duration")
        lines.append("# TYPE pipeline_duration_seconds histogram")
        for stage, metrics in self._stage_metrics.items():
            for bucket in self.BUCKETS:
                count = sum(1 for d in metrics.durations if d <= bucket)
                lines.append(
                    f'pipeline_duration_seconds_bucket{{stage="{stage}",le="{bucket}"}} {count}'
                )
            lines.append(
                f'pipeline_duration_seconds_bucket{{stage="{stage}",le="+Inf"}} '
                f'{len(metrics.durations)}'
            )
            lines.append(
                f'pipeline_duration_seconds_sum{{stage="{stage}"}} '
                f'{metrics.total_duration_seconds}'
            )
            lines.append(
                f'pipeline_duration_seconds_count{{stage="{stage}"}} '
                f'{metrics.records_processed + metrics.records_failed}'
            )
        
        # Errors by type
        lines.append("# HELP pipeline_errors_total Errors by type")
        lines.append("# TYPE pipeline_errors_total counter")
        for stage, metrics in self._stage_metrics.items():
            for error_type, count in metrics.errors_by_type.items():
                lines.append(
                    f'pipeline_errors_total{{stage="{stage}",type="{error_type}"}} {count}'
                )
        
        # Registry skips
        lines.append("# HELP pipeline_registry_skips_total Registry skip events")
        lines.append("# TYPE pipeline_registry_skips_total counter")
        lines.append(f"pipeline_registry_skips_total {self._registry_skips}")
        
        lines.append("# HELP pipeline_registry_checks_total Registry check events")
        lines.append("# TYPE pipeline_registry_checks_total counter")
        lines.append(f"pipeline_registry_checks_total {self._registry_total}")
        
        # Active workers gauge
        lines.append("# HELP pipeline_active_workers Current active worker count")
        lines.append("# TYPE pipeline_active_workers gauge")
        lines.append(f"pipeline_active_workers {self._active_workers}")
        
        # Dead letter queue size
        lines.append("# HELP pipeline_dead_letter_size Dead letter queue size")
        lines.append("# TYPE pipeline_dead_letter_size gauge")
        lines.append(f"pipeline_dead_letter_size {self._dead_letter_size}")
        
        # Uptime
        uptime = time.time() - self._start_time
        lines.append("# HELP pipeline_uptime_seconds Pipeline uptime")
        lines.append("# TYPE pipeline_uptime_seconds gauge")
        lines.append(f"pipeline_uptime_seconds {uptime:.2f}")
        
        return "\n".join(lines)
    
    def to_json(self) -> str:
        """Export metrics as JSON string."""
        return json.dumps(self.get_summary(), indent=2)
    
    def save_to_file(
        self,
        basename: str = "pipeline",
        formats: Optional[list[str]] = None,
    ) -> None:
        """Save metrics to file(s).
        
        Args:
            basename: Base filename without extension
            formats: List of formats to save ("prometheus", "json")
        """
        if not self.metrics_path:
            return
        
        formats = formats or ["prometheus", "json"]
        
        if "prometheus" in formats:
            prom_path = self.metrics_path / f"{basename}.prom"
            prom_path.write_text(self.to_prometheus(), encoding="utf-8")
            logger.debug("Saved Prometheus metrics to %s", prom_path)
        
        if "json" in formats:
            json_path = self.metrics_path / f"{basename}.json"
            json_path.write_text(self.to_json(), encoding="utf-8")
            logger.debug("Saved JSON metrics to %s", json_path)
    
    def log_summary(self) -> None:
        """Log current metrics summary at INFO level."""
        summary = self.get_summary()
        logger.info(
            "Pipeline metrics: processed=%d, failed=%d, skip_rate=%.1f%%, workers=%d",
            summary["total_processed"],
            summary["total_failed"],
            summary["registry_skip_rate_pct"],
            summary["active_workers"],
        )


class _MetricsTimer:
    """Context manager for timing stage execution."""
    
    def __init__(self, metrics: PipelineMetrics, stage: str) -> None:
        self.metrics = metrics
        self.stage = stage
        self.start_time: Optional[float] = None
        self.error: Optional[Exception] = None
    
    def __enter__(self) -> "_MetricsTimer":
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.start_time is None:
            return
        
        duration = time.perf_counter() - self.start_time
        
        if exc_val is not None:
            error_type = exc_type.__name__ if exc_type else "UnknownError"
            self.metrics.record_failure(self.stage, error_type, duration)
        else:
            self.metrics.record_success(self.stage, duration)
