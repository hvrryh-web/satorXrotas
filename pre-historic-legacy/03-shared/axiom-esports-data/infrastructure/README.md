# Axiom Esports Database Infrastructure

PostgreSQL 15 with TimescaleDB for esports analytics, optimized for free-tier cloud deployment.

## Quick Start

### Local Development (Docker)

```bash
cd shared/axiom-esports-data/infrastructure

# Copy environment template
cp .env.example .env

# Start services
docker-compose up -d

# Apply migrations and seed data
./setup.sh          # macOS/Linux
.\setup.ps1         # Windows

# Or with PGAdmin (optional)
docker-compose --profile with-pgadmin up -d
```

### Production (Supabase Recommended)

1. Create project at [supabase.com](https://supabase.com)
2. Get connection string from Settings > Database > Connection string
3. Use Transaction pooler (port 6543) for serverless functions
4. Add to your environment:

```bash
DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
DB_SSL_MODE=require
```

### Production (Neon Alternative)

1. Create project at [neon.tech](https://neon.tech)
2. Use pooled connection string:

```bash
DATABASE_URL=postgresql://[user]:[password]@[project].us-east-1.aws.neon.tech/[db]?sslmode=require
```

## Schema Overview

### Core Tables

| Table | Description |
|-------|-------------|
| `player_performance` | 37-field KCRITR schema with TimescaleDB hypertable |
| `sator_events` | Golden halo event markers (Layer 1) |
| `arepo_markers` | Death stain persistence (Layer 4) |
| `rotas_trails` | Rotation trail data (Layer 5) |
| `web_data_store` | Sanitized public data for web project |

### Staging Tables

| Table | Purpose |
|-------|---------|
| `staging_ingest_queue` | Central ingest queue |
| `staging_static_base` | Versioned static definitions |
| `game_data_store` | RadiantX game project data |
| `raw_extractions` | Immutable raw extraction archive |

## Scripts

| Command | Description |
|---------|-------------|
| `./setup.sh` | Full setup (migrations + seed) |
| `./setup.sh --only-migrations` | Migrations only |
| `./setup.sh --only-seed` | Seeding only |
| `./setup.sh --reset` | Reset and re-seed |
| `./setup.sh --dry-run` | Preview changes |

## Free Tier Optimization

### Connection Pool Settings

```bash
# In .env
DB_POOL_SIZE=5          # Keep low for free tier
DB_MAX_OVERFLOW=2
DB_CONNECT_RETRY_ATTEMPTS=5
```

### SSL Modes

| Provider | Recommended Mode |
|----------|-----------------|
| Supabase Pooler | `require` |
| Supabase Direct | `verify-full` |
| Neon | `require` |
| Local Docker | `prefer` |

## Environment Variables

See `.env.example` for all options. Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Full connection string | - |
| `POSTGRES_HOST` | Database host | localhost |
| `POSTGRES_PORT` | Database port | 5432 |
| `POSTGRES_DB` | Database name | axiom_esports |
| `DB_SSL_MODE` | SSL mode | prefer |
| `DB_POOL_SIZE` | Connection pool size | 5 |

## API Usage

```python
from db import Database

db = Database()
await db.connect()

# Health check
health = await db.health_check()
print(health)  # {'status': 'healthy', 'latency_ms': 12.34}

# Query players
players, total = await db.get_player_list(region="NA", limit=10)

await db.disconnect()
```

## Troubleshooting

### Connection Refused
- Check if PostgreSQL container is running: `docker-compose ps`
- Wait for health check: `docker-compose logs -f postgres`

### SSL Errors
- Set `DB_SSL_MODE=require` for cloud providers
- Set `DB_SSL_MODE=prefer` for local development

### Pool Exhausted
- Reduce `DB_POOL_SIZE` for free tier (max 3-5)
- Enable connection pooling via Supabase/Neon

### Migration Failures
- Ensure migrations run in order (001-005)
- Check TimescaleDB extension is available
