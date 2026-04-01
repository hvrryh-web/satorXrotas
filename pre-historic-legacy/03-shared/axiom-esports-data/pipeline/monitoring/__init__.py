"""
Pipeline Monitoring & Alerting System
======================================

Comprehensive monitoring for the data pipeline with alerting on failures,
anomalies, and data quality issues.

Components:
    - metrics_collector: Prometheus-compatible metrics collection
    - alert_manager: Alert routing and rule evaluation
    - health_reporter: Health check endpoints for load balancers
    - dashboard: Grafana and HTML dashboard generation
    - notifiers: Slack, GitHub, webhook notification channels
    - anomaly_detector: Pattern detection for unusual behavior
    - reports: Pipeline run report generation

Quick Start:
    from pipeline.monitoring import MetricsCollector, AlertManager
    
    metrics = MetricsCollector()
    metrics.record_processed("extraction", 100)
    
    alerts = AlertManager()
    alerts.check_alerts(run_instance)

Integration:
    - Metrics exported at /metrics (Prometheus format)
    - Health checks at /health, /ready, /live
    - Alerts sent via configured channels (Slack, GitHub, webhook)
"""

from pipeline.monitoring.metrics_collector import MetricsCollector
from pipeline.monitoring.alert_manager import AlertManager, Alert, AlertSeverity
from pipeline.monitoring.health_reporter import HealthReporter, HealthReport, HealthStatus
from pipeline.monitoring.dashboard import PipelineDashboard, init_dashboard_app
from pipeline.monitoring.anomaly_detector import AnomalyDetector, DriftReport
from pipeline.monitoring.reports import ReportGenerator, RunReport, DailySummary, WeeklyReport

# Dashboard generator for Grafana/static HTML
from pipeline.monitoring.dashboard_generator import DashboardGenerator, DashboardConfig

__all__ = [
    # Core monitoring
    "MetricsCollector",
    "AlertManager",
    "Alert",
    "AlertSeverity",
    "HealthReporter",
    "HealthReport",
    "HealthStatus",
    "DashboardGenerator",
    "DashboardConfig",
    "PipelineDashboard",
    "init_dashboard_app",
    "AnomalyDetector",
    "DriftReport",
    "ReportGenerator",
    "RunReport",
    "DailySummary",
    "WeeklyReport",
]

__version__ = "1.0.0"
