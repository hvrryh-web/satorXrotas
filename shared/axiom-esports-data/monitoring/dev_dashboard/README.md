# SATOR Developer Dashboard

A comprehensive monitoring system for aggregating health checks across all SATOR platform components with layered views, maintenance scheduling, and alerting.

## Features

- 🔍 **Layered System Views** - Organize components by system layer
- 📊 **Real-time Health Checks** - Automatic monitoring with 30-second refresh
- 🔧 **Maintenance Scheduling** - Schedule windows with notifications
- 🔔 **Smart Alerting** - Rule-based alerts with auto-resolution
- 🖥️ **Web Dashboard** - Dark-themed responsive UI
- 🛠️ **CLI Management** - Command-line tools for administration
- 📈 **Metrics History** - Time-series data with TimescaleDB

## System Layers

| Layer | Components | Icon |
|-------|-----------|------|
| Infrastructure | PostgreSQL, Redis, Storage | 🗄️ |
| API Services | FastAPI, Pipeline Coordinator | 🔌 |
| Data Pipeline | CS Extractor, Valorant Extractor | 📊 |
| Web Platform | Static Website, React Web App | 🌐 |
| Simulation | Godot Engine | 🎮 |
| Security | Firewall, Auth | 🔒 |
| External | Supabase, Render, Vercel | 🔗 |

## Quick Start

### 1. Database Setup

```bash
# Apply migrations
psql $DATABASE_URL -f infrastructure/migrations/008_dashboard_tables.sql
psql $DATABASE_URL -f infrastructure/migrations/009_alert_scheduler_tables.sql
```

### 2. Start Dashboard Server

```bash
cd shared/axiom-esports-data/monitoring/dev_dashboard/web
pip install -r requirements.txt
python app.py
```

Access dashboard at: http://localhost:8095

### 3. CLI Commands

```bash
# Dashboard summary
python -m monitoring.dev_dashboard.cli dashboard summary

# List active alerts
python -m monitoring.dev_dashboard.cli alerts list

# Schedule maintenance
python -m monitoring.dev_dashboard.cli maintenance schedule \
    --title "Database Maintenance" \
    --start "2026-03-10T02:00:00" \
    --duration 120 \
    --layers infrastructure

# Create alert rule
python -m monitoring.dev_dashboard.cli rules create \
    --name "API Latency" \
    --component fastapi_main \
    --condition threshold_exceeded \
    --threshold 500 \
    --severity warning
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DEVELOPER DASHBOARD                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐            │
│  │   Web UI     │   │    API       │   │     CLI      │            │
│  │  (React)     │   │  (FastAPI)   │   │   (Click)    │            │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘            │
│         └───────────────────┼───────────────────┘                    │
│                             │                                        │
│  ┌──────────────────────────▼──────────────────────────┐            │
│  │              Health Check Collectors                 │            │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │            │
│  │  │Database│ │  API   │ │Pipeline│ │Website │ ...   │            │
│  │  └────────┘ └────────┘ └────────┘ └────────┘       │            │
│  └──────────────────────────┬──────────────────────────┘            │
│                             │                                        │
│  ┌──────────────────────────▼──────────────────────────┐            │
│  │               Alert Manager                          │            │
│  │   - Rule evaluation    - Notification routing        │            │
│  │   - Deduplication      - Auto-resolution             │            │
│  └──────────────────────────┬──────────────────────────┘            │
│                             │                                        │
│  ┌──────────────────────────▼──────────────────────────┐            │
│  │            Maintenance Scheduler                     │            │
│  │   - Window scheduling  - Pre-maintenance alerts      │            │
│  │   - Status tracking    - Conflict detection          │            │
│  └──────────────────────────┬──────────────────────────┘            │
│                             │                                        │
│  └──────────────────────────▼──────────────────────────┘            │
│                         PostgreSQL                                   │
│              (TimescaleDB for time-series data)                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Health Check Types

### Database Checks
- ✅ Connection/latency
- 💾 Disk space usage
- 🔄 Replication lag
- 🔌 Active connections
- 🐌 Slow query detection

### API Checks
- ✅ Health endpoint
- 📏 Response latency
- 🔍 Deep health (dependencies)
- 📊 Metrics endpoint

### Pipeline Checks
- 📋 Job queue status
- 📈 Job success rate
- 🕐 Data freshness
- 🤖 Extractor status

### Website Checks
- ✅ Connectivity
- 🔒 SSL certificate
- 📄 Content validation
- 🎨 Static assets
- ⚡ Response time

## Alert Rules

### Conditions
- **Status Change** - Component becomes degraded/critical
- **Threshold Exceeded** - Metric crosses defined threshold
- **Consecutive Failures** - N consecutive check failures

### Severity Levels
| Level | Response Time | Channels |
|-------|--------------|----------|
| Critical | Immediate | Slack + Email + PagerDuty |
| High | 5 minutes | Slack + Email |
| Medium | 15 minutes | Slack |
| Low | 1 hour | Dashboard only |

### Cooldown
Prevents alert spam with configurable cooldown (default: 15 minutes).

## API Reference

### Dashboard Endpoints

```
GET  /                      Dashboard HTML interface
GET  /api/summary           High-level summary
GET  /api/layers            List all layers
GET  /api/layers/{layer}/components   Get layer components
GET  /api/components/{id}/checks      Get component checks
```

### Maintenance Endpoints

```
POST /api/maintenance               Schedule maintenance
GET  /api/maintenance/active        Active windows
GET  /api/maintenance/upcoming      Upcoming windows
PUT  /api/maintenance/{id}/cancel   Cancel scheduled
```

### Alert Endpoints

```
GET  /api/alerts/active             Active alerts
POST /api/alerts/{id}/ack           Acknowledge
POST /api/alerts/{id}/resolve       Resolve
GET  /api/alerts/rules              List rules
POST /api/alerts/rules              Create rule
```

## Configuration

### Environment Variables

```bash
# Database
DASHBOARD_DATABASE_URL=postgresql://localhost/axiom_monitoring

# Server
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8095

# Collection
COLLECTION_INTERVAL_SECONDS=30

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
EMAIL_SMTP_HOST=smtp.gmail.com
PAGERDUTY_SERVICE_KEY=...
```

### Alert Rule Configuration

```yaml
# Example alert rule
rules:
  - name: "Database Connection Lost"
    component: postgres_primary
    condition: status_change
    severity: critical
    channels: [slack, email]
    cooldown_minutes: 5
  
  - name: "High API Latency"
    component: fastapi_main
    check_type: latency
    condition: threshold_exceeded
    threshold: 500  # ms
    severity: warning
    channels: [slack]
    cooldown_minutes: 10
```

## CLI Reference

### Dashboard Commands
```bash
python -m monitoring.dev_dashboard.cli dashboard summary
python -m monitoring.dev_dashboard.cli dashboard layers
```

### Maintenance Commands
```bash
# List maintenance windows
python -m monitoring.dev_dashboard.cli maintenance list

# Schedule new window
python -m monitoring.dev_dashboard.cli maintenance schedule \
    --title "Title" \
    --start "2026-03-10T02:00:00" \
    --end "2026-03-10T04:00:00" \
    --layers infrastructure,api_services \
    --components postgres_primary,fastapi_main \
    --description "Database upgrade" \
    --notify 60,15 \
    --user admin

# Cancel scheduled
python -m monitoring.dev_dashboard.cli maintenance cancel WINDOW-ID

# Show details
python -m monitoring.dev_dashboard.cli maintenance show WINDOW-ID
```

### Alert Commands
```bash
# List active alerts
python -m monitoring.dev_dashboard.cli alerts list
python -m monitoring.dev_dashboard.cli alerts list --severity critical

# Acknowledge
python -m monitoring.dev_dashboard.cli alerts ack ALERT-ID --user john

# Resolve
python -m monitoring.dev_dashboard.cli alerts resolve ALERT-ID --note "Fixed"

# History
python -m monitoring.dev_dashboard.cli alerts history --hours 24
```

### Rule Commands
```bash
# List rules
python -m monitoring.dev_dashboard.cli rules list

# Create
python -m monitoring.dev_dashboard.cli rules create \
    --name "Rule Name" \
    --component component-id \
    --layer infrastructure \
    --check-type connectivity \
    --condition consecutive_failures \
    --consecutive 3 \
    --severity high \
    --channels slack,email \
    --cooldown 15

# Toggle
python -m monitoring.dev_dashboard.cli rules toggle RULE-ID

# Delete
python -m monitoring.dev_dashboard.cli rules delete RULE-ID
```

## Database Schema

### Core Tables
- `component_health_history` - Time-series health data (TimescaleDB hypertable)
- `maintenance_windows` - Scheduled maintenance
- `active_alerts` - Currently firing alerts
- `alert_history` - Archive of resolved alerts
- `alert_rules` - Alert configuration
- `notification_log` - Audit trail of notifications
- `dashboard_sessions` - User sessions
- `dashboard_audit_log` - Action audit trail

### Views
- `active_maintenance_summary` - Active maintenance overview
- `alert_statistics` - Alert metrics and MTTR
- `component_uptime_24h` - 24-hour uptime percentages

## Testing

```bash
# Run tests
pytest monitoring/dev_dashboard/tests/

# Test specific collector
python -c "
from monitoring.dev_dashboard.collectors import DatabaseCollector
from monitoring.dev_dashboard.registry import ComponentRegistry
import asyncio
import asyncpg

async def test():
    pool = await asyncpg.create_pool('postgresql://localhost/axiom')
    registry = ComponentRegistry()
    comp = registry.get('postgres_primary')
    
    async with DatabaseCollector(comp, pool) as collector:
        results = await collector.collect()
        for r in results:
            print(f'{r.name}: {r.status}')

asyncio.run(test())
"
```

## Troubleshooting

### Dashboard not updating
- Check browser console for errors
- Verify WebSocket connection (if using real-time updates)
- Check `/api/summary` endpoint directly

### Health checks failing
- Verify component endpoints are accessible
- Check collector logs: `tail -f logs/dashboard.log`
- Test collector manually (see Testing section)

### Alerts not firing
- Verify alert rules are enabled
- Check cooldown period hasn't expired
- Review alert manager logs

### Maintenance notifications not sent
- Verify scheduler is running
- Check notification channel configuration
- Review notification log table

## License

MIT License - Part of the SATOR Platform
