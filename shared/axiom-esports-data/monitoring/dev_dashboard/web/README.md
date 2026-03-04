# Developer Dashboard Web Interface

A web-based developer dashboard for monitoring SATOR system health with layered views.

## Features

- **Layered Architecture**: View components organized by system layers:
  - 🗄️ Infrastructure (Database, Cache)
  - 🔌 API Services (FastAPI, Pipeline Coordinator)
  - 📊 Data Pipeline (Extractors)
  - 🌐 Web Platform (Static site, React app)
  - 🔒 Security (Firewall, Auth)
  - 🎮 Simulation (Godot, Game Systems)
  - 🔗 External (Third-party services)

- **Real-time Updates**: Auto-refreshes every 30 seconds
- **Responsive Design**: Works on desktop and mobile
- **Component Drill-down**: Click any component for detailed health check information
- **Dark Theme**: Optimized for developer workflows

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL database
- Dependencies from `requirements.txt`:
  ```
  fastapi
  uvicorn
  asyncpg
  pydantic
  aiohttp
  ```

### Run the Dashboard

```bash
# From the dev_dashboard directory
python -m web.app
```

The dashboard will be available at `http://localhost:8095`

### Using Uvicorn Directly

```bash
uvicorn web.app:app --host 0.0.0.0 --port 8095 --reload
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Main dashboard HTML interface |
| `GET /api/summary` | High-level dashboard summary |
| `GET /api/layers` | List all system layers |
| `GET /api/layers/{layer}/components` | Get components for a layer |
| `GET /api/components/{id}/checks` | Get detailed checks for a component |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1-7` | Switch to layer 1-7 |
| `R` | Refresh current view |
| `ESC` | Close modal |

## Architecture

```
┌─────────────────────────────────────────┐
│           Web Dashboard                 │
│  ┌─────────┐  ┌─────────────────────┐   │
│  │ Sidebar │  │   Main Content      │   │
│  │ - Layers│  │  ┌───────────────┐  │   │
│  │ - Quick │  │  │ Stats Grid    │  │   │
│  │   Links │  │  └───────────────┘  │   │
│  └─────────┘  │  ┌───────────────┐  │   │
│               │  │ Components    │  │   │
│               │  │ Grid          │  │   │
│               │  └───────────────┘  │   │
│               └─────────────────────┘   │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│           FastAPI Backend               │
│  ┌──────────┐  ┌─────────────────────┐  │
│  │ Registry │  │ Health Collectors   │  │
│  │ - Models │  │ - Database          │  │
│  │ - Layers │  │ - API               │  │
│  └──────────┘  │ - Pipeline          │  │
│                │ - External          │  │
│                └─────────────────────┘  │
└─────────────────────────────────────────┘
```

## Database Schema

The dashboard uses tables from migration `008_dashboard_tables.sql`:

- `dashboard_sessions` - User sessions and preferences
- `component_health_history` - Time-series health data
- `dashboard_audit_log` - Action audit trail
- `maintenance_windows` - Scheduled maintenance
- `alert_rules` - Configurable alerting rules
- `dashboard_notifications` - User notification queue

## Customization

### Adding a New Layer

1. Add to `SystemLayer` enum in `../models.py`
2. Add icon mapping in `app.py:get_layer_icon()`
3. Register components in `../registry.py`

### Adding a New Collector

1. Create collector class in `../collectors/`
2. Add to `../collectors/__init__.py`
3. Update `get_collector_for_component()` in `app.py`

## Development

### Run Tests

```bash
pytest monitoring/dev_dashboard/tests/
```

### Static Analysis

```bash
mypy web/app.py
pylint web/
```

## License

MIT - See LICENSE file
