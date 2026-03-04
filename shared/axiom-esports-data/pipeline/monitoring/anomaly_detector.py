"""
Anomaly Detector — Detect unusual patterns in pipeline metrics.

Detects:
    - Sudden drops in data volume
    - Unusual error patterns
    - Schema drift detection
    - Performance degradation

Example:
    from pipeline.monitoring import AnomalyDetector
    
    detector = AnomalyDetector()
    
    # Volume anomaly detection
    is_anomaly = detector.detect_volume_anomaly(
        current=500,
        historical=[1000, 1100, 1050, 1080, 1020]
    )
    
    # Schema drift detection
    drift_reports = detector.detect_schema_drift(
        new_record={"new_field": "value"},
        schema=expected_schema
    )
"""

import json
import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class AnomalyType(str, Enum):
    """Types of anomalies that can be detected."""
    VOLUME_DROP = "volume_drop"
    VOLUME_SPIKE = "volume_spike"
    ERROR_RATE_SPIKE = "error_rate_spike"
    LATENCY_SPIKE = "latency_spike"
    SCHEMA_DRIFT = "schema_drift"
    DUPLICATE_SURGE = "duplicate_surge"
    MISSING_DATA = "missing_data"


class DriftType(str, Enum):
    """Types of schema drift."""
    NEW_FIELD = "new_field"
    MISSING_FIELD = "missing_field"
    TYPE_CHANGE = "type_change"
    FORMAT_CHANGE = "format_change"


@dataclass
class DriftReport:
    """Report of a single schema drift."""
    field_path: str
    drift_type: DriftType
    expected: Any
    actual: Any
    severity: str  # low, medium, high
    detected_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "field_path": self.field_path,
            "drift_type": self.drift_type.value,
            "expected": str(self.expected) if self.expected is not None else None,
            "actual": str(self.actual) if self.actual is not None else None,
            "severity": self.severity,
            "detected_at": self.detected_at.isoformat(),
        }


@dataclass
class AnomalyReport:
    """Report of a detected anomaly."""
    anomaly_type: AnomalyType
    severity: str  # low, medium, high, critical
    message: str
    current_value: float
    expected_range: tuple[float, float]
    confidence: float  # 0-1
    context: dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "anomaly_type": self.anomaly_type.value,
            "severity": self.severity,
            "message": self.message,
            "current_value": self.current_value,
            "expected_range": self.expected_range,
            "confidence": self.confidence,
            "context": self.context,
            "detected_at": self.detected_at.isoformat(),
        }


class AnomalyDetector:
    """
    Detect anomalies in pipeline metrics and data.
    
    Uses statistical methods to detect deviations from normal patterns:
        - Z-score for volume anomalies
        - Moving averages for trend detection
        - Schema validation for drift detection
    """
    
    def __init__(
        self,
        volume_threshold_sigma: float = 2.5,
        error_rate_threshold: float = 0.15,
        latency_threshold_sigma: float = 2.0,
        duplicate_rate_threshold: float = 0.25,
        min_historical_points: int = 5,
    ) -> None:
        """
        Initialize anomaly detector.
        
        Args:
            volume_threshold_sigma: Z-score threshold for volume anomalies
            error_rate_threshold: Error rate threshold for anomaly
            latency_threshold_sigma: Z-score threshold for latency anomalies
            duplicate_rate_threshold: Duplicate rate threshold
            min_historical_points: Minimum historical points needed
        """
        self.volume_threshold_sigma = volume_threshold_sigma
        self.error_rate_threshold = error_rate_threshold
        self.latency_threshold_sigma = latency_threshold_sigma
        self.duplicate_rate_threshold = duplicate_rate_threshold
        self.min_historical_points = min_historical_points
    
    def detect_volume_anomaly(
        self,
        current: int,
        historical: list[int],
        direction: str = "both",  # "drop", "spike", "both"
    ) -> Optional[AnomalyReport]:
        """
        Detect if current volume is anomalous vs historical data.
        
        Uses Z-score to detect statistical outliers.
        
        Args:
            current: Current volume value
            historical: List of historical volume values
            direction: Which direction to check
            
        Returns:
            AnomalyReport if anomaly detected, None otherwise
        """
        if len(historical) < self.min_historical_points:
            logger.debug(f"Insufficient historical data: {len(historical)} points")
            return None
        
        mean = statistics.mean(historical)
        stdev = statistics.stdev(historical) if len(historical) > 1 else 0
        
        if stdev == 0:
            # No variance, check absolute difference
            if abs(current - mean) > mean * 0.5:
                return self._create_volume_report(current, mean, mean * 0.5, direction)
            return None
        
        z_score = (current - mean) / stdev
        
        # Check based on direction
        is_drop = z_score < -self.volume_threshold_sigma
        is_spike = z_score > self.volume_threshold_sigma
        
        if direction in ("drop", "both") and is_drop:
            return self._create_volume_report(
                current, mean, stdev, "drop", abs(z_score)
            )
        
        if direction in ("spike", "both") and is_spike:
            return self._create_volume_report(
                current, mean, stdev, "spike", abs(z_score)
            )
        
        return None
    
    def _create_volume_report(
        self,
        current: float,
        mean: float,
        stdev: float,
        direction: str,
        confidence: float = 0.95,
    ) -> AnomalyReport:
        """Create a volume anomaly report."""
        is_drop = direction == "drop"
        pct_change = ((current - mean) / mean * 100) if mean > 0 else 0
        
        return AnomalyReport(
            anomaly_type=AnomalyType.VOLUME_DROP if is_drop else AnomalyType.VOLUME_SPIKE,
            severity="high" if confidence > 3 else "medium",
            message=f"Volume {direction}: {abs(pct_change):.1f}% {'below' if is_drop else 'above'} average",
            current_value=current,
            expected_range=(mean - stdev * 2, mean + stdev * 2),
            confidence=min(confidence / 5, 1.0),
            context={
                "mean": mean,
                "stdev": stdev,
                "percent_change": pct_change,
                "direction": direction,
            },
        )
    
    def detect_error_rate_anomaly(
        self,
        current_rate: float,
        historical_rates: list[float],
    ) -> Optional[AnomalyReport]:
        """
        Detect unusual error rate patterns.
        
        Args:
            current_rate: Current error rate (0-1)
            historical_rates: List of historical error rates
            
        Returns:
            AnomalyReport if anomaly detected
        """
        # Absolute threshold check
        if current_rate > self.error_rate_threshold:
            return AnomalyReport(
                anomaly_type=AnomalyType.ERROR_RATE_SPIKE,
                severity="critical" if current_rate > 0.5 else "high",
                message=f"Error rate spike: {current_rate:.1%}",
                current_value=current_rate,
                expected_range=(0, self.error_rate_threshold),
                confidence=min(current_rate / self.error_rate_threshold, 1.0),
                context={"threshold": self.error_rate_threshold},
            )
        
        # Statistical check if we have history
        if len(historical_rates) >= self.min_historical_points:
            mean = statistics.mean(historical_rates)
            stdev = statistics.stdev(historical_rates) if len(historical_rates) > 1 else 0
            
            if stdev > 0:
                z_score = (current_rate - mean) / stdev
                if z_score > self.volume_threshold_sigma:
                    return AnomalyReport(
                        anomaly_type=AnomalyType.ERROR_RATE_SPIKE,
                        severity="medium",
                        message=f"Error rate {z_score:.1f}σ above average",
                        current_value=current_rate,
                        expected_range=(mean - stdev * 2, mean + stdev * 2),
                        confidence=min(z_score / 5, 1.0),
                        context={"mean": mean, "stdev": stdev, "z_score": z_score},
                    )
        
        return None
    
    def detect_latency_anomaly(
        self,
        current_latency: float,
        historical_latencies: list[float],
    ) -> Optional[AnomalyReport]:
        """
        Detect performance degradation (latency spikes).
        
        Args:
            current_latency: Current latency in seconds
            historical_latencies: List of historical latencies
            
        Returns:
            AnomalyReport if anomaly detected
        """
        if len(historical_latencies) < self.min_historical_points:
            return None
        
        mean = statistics.mean(historical_latencies)
        stdev = statistics.stdev(historical_latencies) if len(historical_latencies) > 1 else 0
        
        if stdev == 0:
            # Check for 2x increase
            if current_latency > mean * 2:
                return AnomalyReport(
                    anomaly_type=AnomalyType.LATENCY_SPIKE,
                    severity="high" if current_latency > mean * 3 else "medium",
                    message=f"Latency increased {current_latency/mean:.1f}x",
                    current_value=current_latency,
                    expected_range=(0, mean * 1.5),
                    confidence=0.8,
                    context={"mean_latency": mean, "multiplier": current_latency / mean},
                )
            return None
        
        z_score = (current_latency - mean) / stdev
        
        if z_score > self.latency_threshold_sigma:
            return AnomalyReport(
                anomaly_type=AnomalyType.LATENCY_SPIKE,
                severity="high" if z_score > 3 else "medium",
                message=f"Latency spike: {current_latency:.2f}s ({z_score:.1f}σ above avg)",
                current_value=current_latency,
                expected_range=(0, mean + stdev * 2),
                confidence=min(z_score / 5, 1.0),
                context={"mean": mean, "stdev": stdev, "z_score": z_score},
            )
        
        return None
    
    def detect_schema_drift(
        self,
        new_record: dict,
        schema: dict,
        strict_types: bool = False,
    ) -> list[DriftReport]:
        """
        Detect unexpected fields or type changes in records.
        
        Args:
            new_record: The record to check
            schema: Expected schema definition
            strict_types: Whether to enforce strict type checking
            
        Returns:
            List of drift reports
        """
        drifts: list[DriftReport] = []
        
        # Check for missing required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in new_record:
                drifts.append(DriftReport(
                    field_path=field,
                    drift_type=DriftType.MISSING_FIELD,
                    expected="required",
                    actual=None,
                    severity="high",
                ))
        
        # Check for extra fields
        allowed_fields = set(schema.get("properties", {}).keys())
        allowed_fields.update(schema.get("optional", []))
        
        for field in new_record.keys():
            if field not in allowed_fields:
                drifts.append(DriftReport(
                    field_path=field,
                    drift_type=DriftType.NEW_FIELD,
                    expected=None,
                    actual=type(new_record[field]).__name__,
                    severity="medium",
                ))
        
        # Check type mismatches
        if strict_types:
            properties = schema.get("properties", {})
            for field, value in new_record.items():
                if field in properties:
                    expected_type = properties[field].get("type")
                    if expected_type:
                        actual_type = self._python_type_to_json(type(value))
                        if actual_type != expected_type:
                            drifts.append(DriftReport(
                                field_path=field,
                                drift_type=DriftType.TYPE_CHANGE,
                                expected=expected_type,
                                actual=actual_type,
                                severity="medium",
                            ))
        
        return drifts
    
    def _python_type_to_json(self, py_type: type) -> str:
        """Convert Python type to JSON schema type."""
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }
        return type_map.get(py_type, "unknown")
    
    def detect_duplicate_surge(
        self,
        current_rate: float,
        historical_rates: list[float],
    ) -> Optional[AnomalyReport]:
        """
        Detect unusual increase in duplicate rate.
        
        Args:
            current_rate: Current duplicate rate (0-1)
            historical_rates: List of historical duplicate rates
            
        Returns:
            AnomalyReport if surge detected
        """
        # Absolute threshold
        if current_rate > self.duplicate_rate_threshold:
            return AnomalyReport(
                anomaly_type=AnomalyType.DUPLICATE_SURGE,
                severity="high" if current_rate > 0.5 else "medium",
                message=f"Duplicate surge: {current_rate:.1%} of records",
                current_value=current_rate,
                expected_range=(0, self.duplicate_rate_threshold),
                confidence=min(current_rate / self.duplicate_rate_threshold, 1.0),
                context={"threshold": self.duplicate_rate_threshold},
            )
        
        # Statistical check
        if len(historical_rates) >= self.min_historical_points:
            mean = statistics.mean(historical_rates)
            if current_rate > mean * 3 and current_rate > 0.1:
                return AnomalyReport(
                    anomaly_type=AnomalyType.DUPLICATE_SURGE,
                    severity="medium",
                    message=f"Duplicate rate {current_rate/mean:.1f}x above average",
                    current_value=current_rate,
                    expected_range=(0, mean * 2),
                    confidence=0.7,
                    context={"mean_rate": mean, "multiplier": current_rate / mean if mean > 0 else 0},
                )
        
        return None
    
    def detect_missing_data(
        self,
        expected_count: int,
        actual_count: int,
        source: str = "unknown",
    ) -> Optional[AnomalyReport]:
        """
        Detect missing or incomplete data.
        
        Args:
            expected_count: Expected number of records
            actual_count: Actual number of records
            source: Data source name
            
        Returns:
            AnomalyReport if data is missing
        """
        if expected_count <= 0:
            return None
        
        missing_pct = (expected_count - actual_count) / expected_count
        
        if missing_pct > 0.1:  # >10% missing
            severity = "critical" if missing_pct > 0.5 else "high" if missing_pct > 0.25 else "medium"
            return AnomalyReport(
                anomaly_type=AnomalyType.MISSING_DATA,
                severity=severity,
                message=f"Missing data from {source}: {missing_pct:.1%} ({expected_count - actual_count} records)",
                current_value=actual_count,
                expected_range=(expected_count * 0.9, expected_count * 1.1),
                confidence=min(missing_pct * 2, 1.0),
                context={
                    "source": source,
                    "expected": expected_count,
                    "actual": actual_count,
                    "missing_count": expected_count - actual_count,
                },
            )
        
        return None
    
    def analyze_run(
        self,
        run_stats: dict,
        historical_stats: list[dict],
    ) -> list[AnomalyReport]:
        """
        Comprehensive anomaly analysis for a pipeline run.
        
        Args:
            run_stats: Current run statistics
            historical_stats: List of historical run statistics
            
        Returns:
            List of all detected anomalies
        """
        anomalies: list[AnomalyReport] = []
        
        # Volume check
        if "records_processed" in run_stats and historical_stats:
            historical_volumes = [s.get("records_processed", 0) for s in historical_stats]
            anomaly = self.detect_volume_anomaly(
                run_stats["records_processed"],
                historical_volumes,
            )
            if anomaly:
                anomalies.append(anomaly)
        
        # Error rate check
        if "error_rate" in run_stats and historical_stats:
            historical_errors = [s.get("error_rate", 0) for s in historical_stats]
            anomaly = self.detect_error_rate_anomaly(
                run_stats["error_rate"],
                historical_errors,
            )
            if anomaly:
                anomalies.append(anomaly)
        
        # Latency check
        if "duration_seconds" in run_stats and historical_stats:
            historical_durations = [s.get("duration_seconds", 0) for s in historical_stats]
            anomaly = self.detect_latency_anomaly(
                run_stats["duration_seconds"],
                historical_durations,
            )
            if anomaly:
                anomalies.append(anomaly)
        
        # Duplicate check
        if "duplicate_rate" in run_stats and historical_stats:
            historical_dups = [s.get("duplicate_rate", 0) for s in historical_stats]
            anomaly = self.detect_duplicate_surge(
                run_stats["duplicate_rate"],
                historical_dups,
            )
            if anomaly:
                anomalies.append(anomaly)
        
        return anomalies
