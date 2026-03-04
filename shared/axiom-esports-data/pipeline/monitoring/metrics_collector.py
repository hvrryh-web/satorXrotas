"""
Metrics Collector — Prometheus-compatible metrics for the data pipeline.

Tracks throughput, latency, error rates, and data quality metrics
in Prometheus exposition format for scraping by Prometheus or
compatible monitoring systems.

Example:
    metrics = MetricsCollector()
    
    # Record processing
    metrics.record_processed("extraction", 100)
    metrics.record_failed("extraction", error_type="network")
    
    # Time a stage
    with metrics.timed_stage("transformation"):
        transform_data(data)
    
    # Export for Prometheus
    print(metrics.export_prometheus())
"""

import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Callable
from contextlib import contextmanager
from collections import defaultdict


@dataclass
class Counter:
    """Prometheus-style counter metric."""
    name: str
    help_text: str
    labels: list[str] = field(default_factory=list)
    _values: dict[tuple, int] = field(default_factory=lambda: defaultdict(int))
    _lock: threading.Lock = field(default_factory=threading.Lock)
    
    def inc(self, value: int = 1, **label_values) -> None:
        """Increment counter by value."""
        key = tuple(label_values.get(l, "") for l in self.labels)
        with self._lock:
            self._values[key] += value
    
    def get(self, **label_values) -> int:
        """Get current counter value for label combination."""
        key = tuple(label_values.get(l, "") for l in self.labels)
        with self._lock:
            return self._values.get(key, 0)
    
    def export(self) -> str:
        """Export in Prometheus format."""
        lines = [f"# HELP {self.name} {self.help_text}",
                 f"# TYPE {self.name} counter"]
        
        with self._lock:
            for key, value in self._values.items():
                if self.labels:
                    label_str = ",".join(
                        f'{l}="{v}"' for l, v in zip(self.labels, key)
                    )
                    lines.append(f'{self.name}{{{label_str}}} {value}')
                else:
                    lines.append(f'{self.name} {value}')
        
        return "\n".join(lines)


@dataclass
class Gauge:
    """Prometheus-style gauge metric."""
    name: str
    help_text: str
    labels: list[str] = field(default_factory=list)
    _values: dict[tuple, float] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    
    def set(self, value: float, **label_values) -> None:
        """Set gauge to specific value."""
        key = tuple(label_values.get(l, "") for l in self.labels)
        with self._lock:
            self._values[key] = value
    
    def inc(self, value: float = 1, **label_values) -> None:
        """Increment gauge by value."""
        key = tuple(label_values.get(l, "") for l in self.labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0) + value
    
    def dec(self, value: float = 1, **label_values) -> None:
        """Decrement gauge by value."""
        self.inc(-value, **label_values)
    
    def get(self, **label_values) -> float:
        """Get current gauge value."""
        key = tuple(label_values.get(l, "") for l in self.labels)
        with self._lock:
            return self._values.get(key, 0)
    
    def export(self) -> str:
        """Export in Prometheus format."""
        lines = [f"# HELP {self.name} {self.help_text}",
                 f"# TYPE {self.name} gauge"]
        
        with self._lock:
            for key, value in self._values.items():
                if self.labels:
                    label_str = ",".join(
                        f'{l}="{v}"' for l, v in zip(self.labels, key)
                    )
                    lines.append(f'{self.name}{{{label_str}}} {value}')
                else:
                    lines.append(f'{self.name} {value}')
        
        return "\n".join(lines)


@dataclass
class Histogram:
    """Prometheus-style histogram metric with configurable buckets."""
    name: str
    help_text: str
    labels: list[str] = field(default_factory=list)
    buckets: list[float] = field(
        default_factory=lambda: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
    )
    _values: dict[tuple, list[float]] = field(default_factory=lambda: defaultdict(list))
    _sum: dict[tuple, float] = field(default_factory=lambda: defaultdict(float))
    _count: dict[tuple, int] = field(default_factory=lambda: defaultdict(int))
    _lock: threading.Lock = field(default_factory=threading.Lock)
    
    def observe(self, value: float, **label_values) -> None:
        """Observe a value."""
        key = tuple(label_values.get(l, "") for l in self.labels)
        with self._lock:
            self._values[key].append(value)
            self._sum[key] += value
            self._count[key] += 1
    
    def get_count(self, **label_values) -> int:
        """Get total observations count."""
        key = tuple(label_values.get(l, "") for l in self.labels)
        with self._lock:
            return self._count.get(key, 0)
    
    def get_sum(self, **label_values) -> float:
        """Get sum of all observations."""
        key = tuple(label_values.get(l, "") for l in self.labels)
        with self._lock:
            return self._sum.get(key, 0)
    
    def export(self) -> str:
        """Export in Prometheus format."""
        lines = [f"# HELP {self.name} {self.help_text}",
                 f"# TYPE {self.name} histogram"]
        
        with self._lock:
            for key in self._values.keys():
                values = self._values[key]
                label_str = ""
                if self.labels:
                    label_str = ",".join(
                        f'{l}="{v}"' for l, v in zip(self.labels, key)
                    )
                    label_str = "{" + label_str + "}"
                
                # Bucket counts
                for bucket in self.buckets:
                    count = sum(1 for v in values if v <= bucket)
                    bucket_label = f'le="{bucket}"'
                    if label_str:
                        full_label = label_str[:-1] + "," + bucket_label + "}"
                    else:
                        full_label = "{" + bucket_label + "}"
                    lines.append(f'{self.name}_bucket{full_label} {count}')
                
                # +Inf bucket
                if label_str:
                    inf_label = label_str[:-1] + ',le="+Inf"}'
                else:
                    inf_label = '{le="+Inf"}'
                lines.append(f'{self.name}_bucket{inf_label} {len(values)}')
                
                # Sum and count
                lines.append(f'{self.name}_sum{label_str} {self._sum[key]}')
                lines.append(f'{self.name}_count{label_str} {self._count[key]}')
        
        return "\n".join(lines)


class MetricsCollector:
    """
    Collect metrics in Prometheus format for the Axiom pipeline.
    
    Tracks:
        - Throughput: records processed per stage
        - Latency: time spent in each pipeline stage
        - Error rates: failures by stage and error type
        - Data quality: validation pass/fail rates
        - System health: active runs, cache sizes
    
    All metrics are thread-safe and can be scraped by Prometheus.
    """
    
    def __init__(self) -> None:
        """Initialize all pipeline metrics."""
        # Counters
        self.records_processed_total = Counter(
            'axiom_records_processed',
            'Total records processed by the pipeline',
            ['stage']
        )
        self.records_failed_total = Counter(
            'axiom_records_failed',
            'Failed record processing attempts',
            ['stage', 'error_type']
        )
        self.validation_failures_total = Counter(
            'axiom_validation_failures',
            'Schema validation failures',
            ['check_type']
        )
        self.duplicates_detected_total = Counter(
            'axiom_duplicates_detected',
            'Duplicate records detected',
            ['duplicate_type']
        )
        self.alerts_sent_total = Counter(
            'axiom_alerts_sent',
            'Alerts sent by severity',
            ['severity', 'channel']
        )
        
        # Gauges
        self.pipeline_active_runs = Gauge(
            'axiom_pipeline_active_runs',
            'Currently running pipeline instances'
        )
        self.registry_cache_size = Gauge(
            'axiom_registry_cache_size',
            'Number of records in the known record registry'
        )
        self.pipeline_queue_depth = Gauge(
            'axiom_pipeline_queue_depth',
            'Pending records in the processing queue',
            ['queue_type']
        )
        self.data_quality_score = Gauge(
            'axiom_data_quality_score',
            'Overall data quality score (0-100)'
        )
        self.last_success_timestamp = Gauge(
            'axiom_last_success_timestamp',
            'Unix timestamp of last successful run'
        )
        
        # Histograms
        self.stage_duration = Histogram(
            'axiom_stage_duration_seconds',
            'Time spent in each pipeline stage',
            ['stage'],
            buckets=[0.1, 0.5, 1, 2.5, 5, 10, 30, 60, 120, 300]
        )
        self.record_size = Histogram(
            'axiom_record_size_bytes',
            'Size distribution of processed records',
            buckets=[100, 500, 1000, 5000, 10000, 50000, 100000]
        )
        self.db_query_duration = Histogram(
            'axiom_db_query_duration_seconds',
            'Database query duration',
            ['query_type'],
            buckets=[0.001, 0.01, 0.1, 0.5, 1, 2.5, 5]
        )
        
        self._start_time: Optional[float] = None
    
    def record_processed(self, stage: str, count: int = 1) -> None:
        """Record successful record processing."""
        self.records_processed_total.inc(count, stage=stage)
    
    def record_failed(self, stage: str, error_type: str = "unknown") -> None:
        """Record a processing failure."""
        self.records_failed_total.inc(1, stage=stage, error_type=error_type)
    
    def record_validation_failure(self, check_type: str) -> None:
        """Record a validation failure."""
        self.validation_failures_total.inc(1, check_type=check_type)
    
    def record_duplicate(self, duplicate_type: str) -> None:
        """Record a detected duplicate."""
        self.duplicates_detected_total.inc(1, duplicate_type=duplicate_type)
    
    def record_alert(self, severity: str, channel: str) -> None:
        """Record an alert being sent."""
        self.alerts_sent_total.inc(1, severity=severity, channel=channel)
    
    def set_active_runs(self, count: int) -> None:
        """Set the number of active pipeline runs."""
        self.pipeline_active_runs.set(count)
    
    def set_registry_size(self, size: int) -> None:
        """Set the known record registry cache size."""
        self.registry_cache_size.set(size)
    
    def set_queue_depth(self, queue_type: str, depth: int) -> None:
        """Set queue depth for a specific queue type."""
        self.pipeline_queue_depth.set(depth, queue_type=queue_type)
    
    def set_data_quality(self, score: float) -> None:
        """Set the overall data quality score (0-100)."""
        self.data_quality_score.set(max(0, min(100, score)))
    
    def record_last_success(self) -> None:
        """Record the current time as last successful run."""
        self.last_success_timestamp.set(time.time())
    
    @contextmanager
    def timed_stage(self, stage: str):
        """Context manager to time a pipeline stage."""
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            self.stage_duration.observe(duration, stage=stage)
    
    @contextmanager
    def timed_db_query(self, query_type: str):
        """Context manager to time a database query."""
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            self.db_query_duration.observe(duration, query_type=query_type)
    
    def record_size_bytes(self, size: int) -> None:
        """Record the size of a processed record."""
        self.record_size.observe(size)
    
    def export_prometheus(self) -> str:
        """Export all metrics in Prometheus exposition format."""
        lines = [
            "# Axiom Pipeline Metrics",
            f"# Generated at {datetime.utcnow().isoformat()}Z",
            "",
        ]
        
        # Export all counters
        for metric in [
            self.records_processed_total,
            self.records_failed_total,
            self.validation_failures_total,
            self.duplicates_detected_total,
            self.alerts_sent_total,
        ]:
            lines.append(metric.export())
            lines.append("")
        
        # Export all gauges
        for metric in [
            self.pipeline_active_runs,
            self.registry_cache_size,
            self.pipeline_queue_depth,
            self.data_quality_score,
            self.last_success_timestamp,
        ]:
            lines.append(metric.export())
            lines.append("")
        
        # Export all histograms
        for metric in [
            self.stage_duration,
            self.record_size,
            self.db_query_duration,
        ]:
            lines.append(metric.export())
            lines.append("")
        
        return "\n".join(lines)
    
    def get_summary(self) -> dict:
        """Get a summary of current metrics values."""
        return {
            "records_processed": {
                stage: self.records_processed_total.get(stage=stage)
                for stage in ["extraction", "validation", "transformation", "storage"]
            },
            "records_failed": {
                stage: sum(
                    self.records_failed_total.get(stage=stage, error_type=et)
                    for et in ["network", "parse", "validation", "storage", "unknown"]
                )
                for stage in ["extraction", "validation", "transformation", "storage"]
            },
            "active_runs": self.pipeline_active_runs.get(),
            "registry_size": self.registry_cache_size.get(),
            "data_quality": self.data_quality_score.get(),
            "last_success": self.last_success_timestamp.get(),
        }


# Global metrics instance
_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get or create global metrics collector instance."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics
