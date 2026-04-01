# Central Job Coordinator

Production-ready central job coordinator for dual-game esports data collection.

## Overview

The coordinator manages extraction jobs across Counter-Strike and Valorant data sources, providing:

- **Priority-based job queuing** with game isolation and fairness
- **Agent lifecycle management** with health monitoring
- **Conflict resolution** for duplicate jobs and content drift
- **Per-source rate limiting** with adaptive backoff
- **Smart job distribution** with load balancing
- **Comprehensive monitoring** with metrics and health checks

## Architecture

```
coordinator/
├── __init__.py          # Package exports
├── models.py            # Pydantic models for all entities
├── queue_manager.py     # Priority queue management
├── agent_manager.py     # Agent registration and monitoring
├── conflict_resolver.py # Conflict detection and resolution
├── rate_limiter.py      # Per-source rate limiting
├── distributor.py       # Job distribution logic
├── monitoring.py        # Metrics and health checks
├── main.py              # FastAPI application
└── migrations/          # Database migrations
    └── 001_initial.sql
```

## Quick Start

### Installation

```bash
pip install fastapi uvicorn pydantic
```

### Database Setup

Run the initial migration:

```bash
psql -d your_database -f coordinator/migrations/001_initial.sql
```

### Running the API

```bash
python -m coordinator.main
```

Or with uvicorn directly:

```bash
uvicorn coordinator.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Job Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/jobs` | Create a new extraction job |
| POST | `/jobs/batch` | Create multiple jobs |
| GET | `/jobs/{job_id}` | Get job details |
| POST | `/jobs/{job_id}/cancel` | Cancel a pending job |

### Agent Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/agents/register` | Register a new agent |
| POST | `/agents/{agent_id}/heartbeat` | Agent heartbeat |
| POST | `/agents/{agent_id}/jobs/{job_id}/complete` | Report job completion |
| GET | `/agents` | List all agents |
| GET | `/agents/{agent_id}` | Get agent details |
| DELETE | `/agents/{agent_id}` | Unregister an agent |

### Queue & Rate Limiting

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/queue/stats` | Get queue statistics |
| POST | `/queue/rebalance` | Trigger rebalancing |
| GET | `/rate-limits/{source}` | Get rate limit status |
| GET | `/rate-limits` | Get all rate limits |
| POST | `/rate-limits/{source}/reset` | Reset rate limit |

### Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Comprehensive health check |
| GET | `/health/ready` | Kubernetes readiness probe |
| GET | `/health/live` | Kubernetes liveness probe |
| GET | `/metrics` | Coordinator metrics |
| GET | `/metrics/prometheus` | Prometheus-format metrics |
| GET | `/status` | Overall coordinator status |

### Administration

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/admin/purge` | Purge old jobs |
| GET | `/admin/distributor/stats` | Distributor statistics |
| GET | `/admin/distributor/insights` | Performance insights |

## Usage Examples

### Creating a Job

```python
import requests

response = requests.post("http://localhost:8000/jobs", json={
    "game": "cs",
    "source": "hltv",
    "job_type": "match_list",
    "priority": 8,
    "epoch": 1,
    "region": "eu"
})

job_id = response.json()["job_id"]
```

### Registering an Agent

```python
response = requests.post("http://localhost:8000/agents/register", json={
    "agent_id": "extractor-001",
    "game_specialization": ["cs", "valorant"],
    "source_capabilities": ["hltv", "vlr"]
})
```

### Agent Heartbeat (Get Work)

```python
response = requests.post("http://localhost:8000/agents/extractor-001/heartbeat")
data = response.json()

if data["assigned_job"]:
    job = data["assigned_job"]
    # Process job...
```

### Reporting Job Completion

```python
requests.post(
    f"http://localhost:8000/agents/extractor-001/jobs/{job_id}/complete",
    json={
        "success": True,
        "records_extracted": 50,
        "checksum": "abc123..."
    }
)
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8000 | API server port |
| `HOST` | 0.0.0.0 | API server host |
| `DATABASE_URL` | - | PostgreSQL connection string |
| `REDIS_URL` | - | Redis connection string (optional) |

## Rate Limits by Source

| Source | Requests/min | Requests/hour | Burst |
|--------|-------------|---------------|-------|
| HLTV | 30 | 500 | 5 |
| VLR | 60 | 2000 | 10 |
| Liquipedia | 30 | 300 | 5 |
| ESL | 100 | 3000 | 20 |
| BLAST | 60 | 1000 | 10 |
| PGL | 60 | 1000 | 10 |
| FACEIT | 120 | 5000 | 20 |
| Riot | 100 | 3000 | 15 |

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
black coordinator/
isort coordinator/
flake8 coordinator/
```

## License

MIT License - See LICENSE file for details.
