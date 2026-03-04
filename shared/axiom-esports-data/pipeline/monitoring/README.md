# Pipeline Monitoring & Alerting System

Comprehensive monitoring for the Axiom data pipeline with alerting on failures, anomalies, and data quality issues.

## Overview

The monitoring system provides:

- **Metrics Collection**: Prometheus-compatible metrics (throughput, latency, error rates)
- **Alert Management**: Rule-based alerting with multiple notification channels
- **Health Checks**: Kubernetes-style probes for load balancer integration
- **Anomaly Detection**: Statistical detection of unusual patterns
- **Reporting**: Daily/weekly pipeline reports
- **Dashboards**: Grafana and HTML dashboard generation

## Quick Start

```python
from pipeline.monitoring import (
    MetricsCollector, AlertManager, HealthReporter,
    AnomalyDetector, DashboardGenerator
)

# Initialize components
metrics = MetricsCollector()
alerts = AlertManager()
health = HealthReporter(db_connection=db)
detector = AnomalyDetector()
dashboard = DashboardGenerator()

# Record metrics
metrics.record_processed("extraction", 100)

# Check health
report = health.get_health()
print(f"Status: {report.status}")  # healthy, degraded, or unhealthy

# Detect anomalies
is_anomaly = detector.detect_volume_anomaly(
    current=500,
    historical=[1000, 1100, 1050, 1080, 1020]
)

# Generate dashboard
html = dashboard.generate_html_dashboard(metrics.get_summary())
```

### Real-time Dashboard & CLI

```bash
# Start the real-time web dashboard
python pipeline/monitoring/dashboard.py --db-url postgresql://localhost/axiom

# Use CLI for queue management
python pipeline/monitoring/queue_cli.py status
python pipeline/monitoring/queue_cli.py queue --game cs
python pipeline/monitoring/queue_cli.py retry --job-id <uuid>
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Pipeline Monitoring                       │
├─────────────────────────────────────────────────────────────┤
│  MetricsCollector  │  AlertManager  │  HealthReporter      │
│  ───────────────── │  ───────────── │  ─────────────────   │
│  - Counters        │  - Rules       │  - /health           │
│  - Gauges          │  - Routing     │  - /ready            │
│  - Histograms      │  - Cooldowns   │  - /live             │
└────────────────┬───┴────────┬───────┴────────┬─────────────┘
                 │            │                │
                 ▼            ▼                ▼
        ┌────────────┐  ┌─────────┐    ┌──────────────┐
        │ Prometheus │  │ Notifiers│    │ Load Balancer│
        │ /metrics   │  │ - Slack │    │ Health Checks│
        └────────────┘  │ - GitHub│    └──────────────┘
                        │ - Email │
                        └─────────┘
```

## Components

### 1. Metrics Collector (`metrics_collector.py`)

Tracks pipeline performance in Prometheus format:

**Counters:**
- `axiom_records_processed_total` - Records by stage
- `axiom_records_failed_total` - Failures by stage/error type
- `axiom_validation_failures_total` - Validation failures
- `axiom_duplicates_detected_total` - Duplicates by type
- `axiom_alerts_sent_total` - Alerts by severity/channel

**Gauges:**
- `axiom_pipeline_active_runs` - Active pipeline instances
- `axiom_registry_cache_size` - Known record registry size
- `axiom_pipeline_queue_depth` - Pending records
- `axiom_data_quality_score` - Overall quality (0-100)
- `axiom_last_success_timestamp` - Unix timestamp

**Histograms:**
- `axiom_stage_duration_seconds` - Time per stage
- `axiom_record_size_bytes` - Record size distribution
- `axiom_db_query_duration_seconds` - Query latency

**Usage:**
```python
from pipeline.monitoring import MetricsCollector

metrics = MetricsCollector()

# Record processing
metrics.record_processed("extraction", 100)

# Time a stage
with metrics.timed_stage("transformation"):
    transform_data(data)

# Export Prometheus format
prom_output = metrics.export_prometheus()
```

### 2. Alert Manager (`alert_manager.py`)

Rule-based alerting with configurable channels.

**Built-in Rules:**
- `pipeline_failure` - Run failed (critical)
- `high_error_rate` - >10% errors (warning)
- `data_quality_drop` - >5% validation failures (warning)
- `stuck_pipeline` - Running >1 hour (warning)
- `duplicate_surge` - >20% duplicates (info)
- `no_recent_success` - No success in 2+ hours (critical)

**Usage:**
```python
from pipeline.monitoring import AlertManager

manager = AlertManager(
    slack_webhook="https://hooks.slack.com/...",
    github_token="ghp_...",
    github_repo="owner/repo",
)

# Check all rules
alerts = manager.check_alerts(run_instance)

# Get active alerts
active = manager.get_active_alerts()

# Resolve an alert
manager.resolve_alert("pipeline_failure", run_id="run_001")
```

### 3. Health Reporter (`health_reporter.py`)

Kubernetes-style health probes.

**Endpoints:**
- `GET /health` - Full health report
- `GET /ready` - Readiness probe
- `GET /live` - Liveness probe

**Usage:**
```python
from pipeline.monitoring import HealthReporter

reporter = HealthReporter(db_connection=conn)

# Full health check
health = reporter.get_health()
# Returns: HealthState.HEALTHY, DEGRADED, or UNHEALTHY

# Kubernetes probes
readiness = reporter.get_readiness()  # Returns HealthStatus
liveness = reporter.get_liveness()
```

### 4. Anomaly Detector (`anomaly_detector.py`)

Statistical anomaly detection.

**Detection Types:**
- Volume anomalies (drop/spike)
- Error rate spikes
- Latency degradation
- Schema drift
- Duplicate surges
- Missing data

**Usage:**
```python
from pipeline.monitoring import AnomalyDetector

detector = AnomalyDetector()

# Volume anomaly
anomaly = detector.detect_volume_anomaly(
    current=500,
    historical=[1000, 1100, 1050, 1080, 1020]
)

# Schema drift
drifts = detector.detect_schema_drift(
    new_record={"unexpected_field": "value"},
    schema=expected_schema
)
```

### 5. Dashboard Generator (`dashboard_generator.py`)

Generate monitoring dashboards.

**Usage:**
```python
from pipeline.monitoring import DashboardGenerator

generator = DashboardGenerator()

# Grafana dashboard
grafana_json = generator.generate_grafana_dashboard()
generator.export_grafana_json("dashboard.json")

# HTML dashboard
html = generator.generate_html_dashboard(metrics_data)
generator.export_html("dashboard.html", metrics_data)
```

### 6. Real-time Pipeline Dashboard (`dashboard.py`)

Web-based real-time monitoring dashboard for the dual-game extraction pipeline.

**Features:**
- Live queue depth and health for both CS and Valorant
- Agent status and performance metrics
- Conflict detection statistics
- Data freshness monitoring by game and source
- Auto-refreshing HTML interface
- REST API for programmatic access

**Running the Dashboard:**
```bash
# Start the dashboard server
python pipeline/monitoring/dashboard.py --db-url postgresql://localhost/axiom --port 8090

# Access the dashboard
open http://localhost:8090
```

**API Endpoints:**
| Endpoint | Description |
|----------|-------------|
| `GET /` | HTML dashboard interface |
| `GET /api/overview` | Pipeline overview (queues, agents, conflicts, freshness) |
| `GET /api/queue?game=cs` | Detailed queue information |
| `GET /api/agents` | Agent status summary |
| `GET /api/failed?game=cs&hours=24` | Recently failed jobs |
| `GET /api/stats?hours=24` | Processing statistics |
| `GET /api/health` | Health check endpoint |

**Programmatic Usage:**
```python
from pipeline.monitoring import PipelineDashboard, init_dashboard_app
import asyncpg

# Create dashboard instance
db_pool = await asyncpg.create_pool("postgresql://localhost/axiom")
dashboard = PipelineDashboard(db_pool, coordinator_url="http://localhost:8080")

# Get pipeline overview
overview = await dashboard.get_overview()
print(f"CS Queue: {overview['queues']['cs']}")
print(f"Agents: {overview['agents']}")

# Get detailed queue
queue = await dashboard.get_detailed_queue(game='cs')

# Get failed jobs
failed = await dashboard.get_failed_jobs(game='valorant', hours=48)

# Get processing stats
stats = await dashboard.get_processing_stats(hours=24)

# Run web server
app = await init_dashboard_app(db_pool, coordinator_url)
```

### 7. Queue Management CLI (`queue_cli.py`)

Command-line interface for queue administration and monitoring.

**Commands:**
```bash
# Pipeline status overview
python pipeline/monitoring/queue_cli.py status

# Queue inspection
python pipeline/monitoring/queue_cli.py queue --game cs --limit 50
python pipeline/monitoring/queue_cli.py queue --game valorant

# Job management
python pipeline/monitoring/queue_cli.py jobs --failed --hours 24
python pipeline/monitoring/queue_cli.py job <job_id>
python pipeline/monitoring/queue_cli.py retry --job-id <uuid>
python pipeline/monitoring/queue_cli.py cancel --job-id <uuid> --reason "Maintenance"
python pipeline/monitoring/queue_cli.py prioritize --job-id <uuid> --priority 10

# Agent management
python pipeline/monitoring/queue_cli.py agents
python pipeline/monitoring/queue_cli.py agents --offline
python pipeline/monitoring/queue_cli.py agent <agent_id>

# Conflict resolution
python pipeline/monitoring/queue_cli.py conflicts
python pipeline/monitoring/queue_cli.py conflicts --game cs --type duplicate
python pipeline/monitoring/queue_cli.py resolve --conflict-id <uuid> --resolution source_a

# Statistics
python pipeline/monitoring/queue_cli.py stats --hours 24
python pipeline/monitoring/queue_cli.py stats --hours 48 --game valorant
```

**CLI Options:**
```bash
python pipeline/monitoring/queue_cli.py --db-url postgresql://user:pass@host/db \
                                        --coordinator http://localhost:8080 \
                                        status
```

### 8. Report Generator (`reports.py`)

Generate pipeline reports.

**Usage:**
```python
from pipeline.monitoring import ReportGenerator
from datetime import date

generator = ReportGenerator(db_connection=conn)

# Single run report
run_report = generator.generate_run_report("run_2024_001")
print(run_report.to_markdown())

# Daily summary
daily = generator.generate_daily_summary(date.today())

# Weekly report
weekly = generator.generate_weekly_report(week=42)

# Export
generator.export_report(daily, Path("daily_report.md"), format="markdown")
```

## Prometheus Integration

### 1. Export Metrics

```python
from flask import Flask
from pipeline.monitoring import get_metrics

app = Flask(__name__)

@app.route('/metrics')
def metrics():
    return get_metrics().export_prometheus()
```

### 2. Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'axiom-pipeline'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 30s
    metrics_path: /metrics
```

### 3. Alert Rules

```yaml
# prometheus_alerts.yml
groups:
  - name: axiom-pipeline
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(axiom_records_failed_total[5m])) 
          / sum(rate(axiom_records_processed_total[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate in pipeline"
          
      - alert: PipelineStuck
        expr: axiom_pipeline_active_runs > 0
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Pipeline has been running for over 1 hour"
          
      - alert: NoRecentSuccess
        expr: time() - axiom_last_success_timestamp > 7200
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "No successful pipeline runs in 2+ hours"
```

## Grafana Integration

### 1. Import Dashboard

1. Generate the dashboard JSON:
```python
from pipeline.monitoring import DashboardGenerator

generator = DashboardGenerator()
dashboard = generator.generate_grafana_dashboard()
```

2. Import into Grafana:
   - Go to Dashboards → Import
   - Paste the JSON or upload the file

### 2. Panel Overview

The generated dashboard includes:

| Section | Panels |
|---------|--------|
| Overview | Records Processed, Error Rate, Active Runs, Data Quality |
| Throughput | Records by Stage, Stage Duration Distribution |
| Data Quality | Validation Failures, Duplicates, Queue Depth |
| System Health | DB Query Duration, Registry Size, Last Success |

### 3. Custom Dashboard

```python
config = DashboardConfig(
    title="My Pipeline Dashboard",
    datasource="my-prometheus",
    refresh_interval="10s"
)
generator = DashboardGenerator(config)
```

## Notification Channels

### Slack

1. Create a webhook in Slack: https://api.slack.com/messaging/webhooks
2. Configure the notifier:
```python
manager = AlertManager(
    slack_webhook="https://hooks.slack.com/services/..."
)
```

### GitHub Issues

1. Create a personal access token with `repo` scope
2. Configure:
```python
manager = AlertManager(
    github_token="ghp_...",
    github_repo="owner/repo"
)
```

### PagerDuty

1. Create a new integration in PagerDuty
2. Configure:
```python
from pipeline.monitoring.notifiers import PagerDutyNotifier

pagerduty = PagerDutyNotifier(
    integration_key="your-integration-key"
)
```

### Generic Webhook

```python
from pipeline.monitoring.notifiers import WebhookNotifier

webhook = WebhookNotifier(
    webhook_url="https://my-service.com/webhooks",
    headers={"Authorization": "Bearer token123"}
)
```

## Database Schema

The monitoring system uses these tables:

### pipeline_runs
Tracks all pipeline executions.

```sql
SELECT * FROM pipeline_runs 
WHERE started_at >= NOW() - INTERVAL '24 hours'
ORDER BY started_at DESC;
```

### pipeline_alerts
Alert history and status.

```sql
-- Active alerts
SELECT * FROM v_active_alerts;

-- Alert summary
SELECT * FROM get_active_alerts_summary();
```

### anomaly_log
Detected anomalies for analysis.

```sql
-- Recent anomalies
SELECT * FROM v_recent_anomalies;

-- False positives to review
SELECT * FROM anomaly_log 
WHERE reviewed_at IS NULL 
  AND false_positive = FALSE;
```

### health_check_log
Historical health check results.

```sql
-- Health trends
SELECT DATE(checked_at), overall_status, COUNT(*)
FROM health_check_log
GROUP BY DATE(checked_at), overall_status;
```

## Configuration

See `config/alerts.yaml` for full configuration options:

```yaml
rules:
  pipeline_failure:
    enabled: true
    condition: 'run.status == "failed"'
    severity: critical
    channels: [slack, github]

channels:
  slack:
    enabled: true
    webhook_url: "${SLACK_WEBHOOK_URL}"

anomaly_detection:
  volume:
    threshold_sigma: 2.5
```

Copy to `alerts.local.yaml` and customize for your environment.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL |
| `GITHUB_TOKEN` | GitHub personal access token |
| `GITHUB_REPO` | GitHub repo (owner/repo format) |
| `PAGERDUTY_KEY` | PagerDuty integration key |
| `ALERT_WEBHOOK_URL` | Generic webhook URL |

## Testing

Run the monitoring system tests:

```bash
# All monitoring tests
pytest pipeline/monitoring/tests/

# Specific component
pytest pipeline/monitoring/tests/test_alert_manager.py
```

## Troubleshooting

### Metrics not appearing in Prometheus

1. Check metrics endpoint: `curl http://localhost:9090/metrics`
2. Verify Prometheus target is up in Prometheus UI
3. Check scrape_interval is appropriate

### Alerts not sending

1. Check alert rules: `manager.check_alerts(run)`
2. Verify notifier configuration
3. Check alert history: `manager.get_alert_history()`
4. Review cooldown periods

### Health checks failing

1. Check individual components: `health.get_health().components`
2. Verify database connectivity
3. Check disk space: `health._check_disk_space()`

## License

Part of the Axiom Esports Data Pipeline system.
