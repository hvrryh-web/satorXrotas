# Axiom Pipeline

Production scheduling and execution system for the Axiom Esports data pipeline.

## Features

- **Multiple Trigger Types**: Cron schedules, webhooks, manual triggers, event-based
- **Full Lifecycle Management**: Start, monitor, cancel, and retry pipeline runs
- **Persistent State**: PostgreSQL storage for runs, schedules, and checkpoints
- **Background Daemon**: Runs scheduled jobs and handles webhooks
- **Rich CLI**: Complete command-line interface for all operations
- **Health Monitoring**: Built-in health checks and metrics

## Installation

```bash
cd shared/axiom-esports-data
pip install -e .
```

Or install from requirements:

```bash
pip install -r requirements-pipeline.txt
```

## Database Setup

Initialize the database schema:

```bash
# Using psql
psql $DATABASE_URL -f pipeline/schema.sql

# Or via CLI (auto-initializes on first run)
axiom-pipeline status
```

## Quick Start

### 1. Run a Pipeline

```bash
# Run in delta mode
axiom-pipeline run --mode=delta --epochs=1,2,3

# Run with logs
axiom-pipeline run --mode=full --follow
```

### 2. Schedule a Job

```bash
# Daily at 6 AM
axiom-pipeline schedule add --name=daily-delta --cron="0 6 * * *" --mode=delta

# Webhook-triggered job
axiom-pipeline schedule add --name=webhook-job --webhook --mode=delta

# List schedules
axiom-pipeline schedule list
```

### 3. Start the Daemon

```bash
# Foreground mode
axiom-pipeline daemon --host 0.0.0.0 --port 8080

# Or use systemd (see axiom-pipeline.service)
sudo systemctl start axiom-pipeline
```

### 4. Check Status

```bash
axiom-pipeline status
axiom-pipeline logs --run-id=<id> --follow
```

## CLI Reference

### Run Commands

```bash
axiom-pipeline run [OPTIONS]
  -m, --mode TEXT          Pipeline mode (delta, full, backfill)
  -e, --epochs TEXT        Epochs to process (default: 1,2,3)
  -b, --batch-size INTEGER Batch size (default: 100)
  -w, --max-workers INTEGER Max workers (default: 3)
  -f, --follow            Follow logs
```

### Schedule Commands

```bash
axiom-pipeline schedule add [OPTIONS]
  -n, --name TEXT         Job name (required)
  -c, --cron TEXT         Cron expression
  -m, --mode TEXT         Pipeline mode
  -e, --epochs TEXT       Epochs
  -d, --description TEXT  Job description
  --webhook              Create webhook job
  --event-type TEXT      Event type for event jobs

axiom-pipeline schedule list [--status active|paused|disabled|error]

axiom-pipeline schedule pause --name=<name>
axiom-pipeline schedule resume --name=<name>
axiom-pipeline schedule delete --name=<name>
```

### Other Commands

```bash
axiom-pipeline status              # Check pipeline status
axiom-pipeline logs --run-id=<id>  # View run logs
axiom-pipeline retry --run-id=<id> # Retry failed run
axiom-pipeline cancel --run-id=<id># Cancel running pipeline
axiom-pipeline daemon [OPTIONS]    # Run daemon
axiom-pipeline webhook-test        # Test webhook
```

## API Endpoints (Daemon)

When the daemon is running, it exposes these HTTP endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/status` | GET | Detailed status |
| `/webhook/{secret}` | POST | Webhook trigger |
| `/trigger/manual` | POST | Manual trigger |
| `/runs` | GET | List runs |
| `/runs/{id}` | GET | Get run details |
| `/runs/{id}/logs` | GET | Get run logs |
| `/runs/{id}/cancel` | POST | Cancel run |
| `/jobs` | GET | List scheduled jobs |
| `/jobs/{id}/pause` | POST | Pause job |
| `/jobs/{id}/resume` | POST | Resume job |

### Example API Usage

```bash
# Health check
curl http://localhost:8080/health

# Trigger manual run
curl -X POST http://localhost:8080/trigger/manual \
  -H "Content-Type: application/json" \
  -d '{"pipeline_args": {"mode": "delta"}}'

# Webhook trigger
curl -X POST http://localhost:8080/webhook/<secret> \
  -H "Content-Type: application/json" \
  -d '{"event": "match_completed"}'
```

## Python API

### Scheduler

```python
from pipeline.scheduler import PipelineScheduler
from pipeline.state_store import StateStore

store = await StateStore().connect()
scheduler = PipelineScheduler(state_store=store)

# Schedule cron job
job = await scheduler.schedule_cron(
    name='daily-delta',
    cron='0 6 * * *',
    pipeline_args={'mode': 'delta', 'epochs': [1, 2, 3]}
)

# Create webhook job
webhook_job = await scheduler.create_webhook_job(
    name='webhook-trigger',
    pipeline_args={'mode': 'delta'}
)
print(f"Webhook secret: {webhook_job.webhook_secret}")

# Trigger manually
run_id = await scheduler.trigger_manual({'mode': 'full'})

# List jobs
jobs = await scheduler.list_scheduled_jobs()

# Pause/Resume
await scheduler.pause_job(job.job_id)
await scheduler.resume_job(job.job_id)
```

### Runner

```python
from pipeline.runner import PipelineRunner
from pipeline.config import PipelineConfig

runner = PipelineRunner(state_store=store)

# Start run
config = PipelineConfig(mode='delta', epochs=[1, 2, 3])
run = await runner.start_run(config, trigger_type=TriggerType.MANUAL)

# Check status
status = runner.get_run_status(run.run_id)

# Get logs
logs = await runner.get_run_logs(run.run_id)

# Cancel
await runner.cancel_run(run.run_id)

# Retry
new_run = await runner.retry_run(run.run_id)
```

### Daemon

```python
from pipeline.daemon import PipelineDaemon

daemon = PipelineDaemon(host='0.0.0.0', port=8080)
await daemon.start()  # Runs until stopped
```

## Systemd Service

See `axiom-pipeline.service` for systemd configuration.

```bash
# Install service
sudo cp pipeline/axiom-pipeline.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable axiom-pipeline
sudo systemctl start axiom-pipeline

# View logs
sudo journalctl -u axiom-pipeline -f
```

## Database Schema

See `pipeline/schema.sql` for the complete PostgreSQL schema.

Key tables:
- `pipeline_runs` - All pipeline runs
- `pipeline_run_logs` - Detailed logs
- `pipeline_scheduled_jobs` - Job configurations
- `pipeline_checkpoints` - Progress checkpoints
- `pipeline_triggers` - Audit trail
- `pipeline_daemon_metrics` - Daemon metrics

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `PIPELINE_MODE` | Default pipeline mode | delta |
| `PIPELINE_EPOCHS` | Default epochs | 1,2,3 |
| `PIPELINE_LOG_LEVEL` | Log level | INFO |
| `PIPELINE_ENABLE_METRICS` | Enable metrics | true |

## License

MIT
