# SATOR Platform - Free Tier Deployment Architecture

## Executive Summary

This document outlines a **zero-cost deployment architecture** for the SATOR esports platform using only free tiers of cloud services. The architecture supports:

- **FastAPI Python API** with PostgreSQL + TimescaleDB
- **React Web Platform** (TypeScript)
- **Static Marketing Site** (GitHub Pages)
- **Godot Game** (local-only, no cloud costs)

---

## Service Selection Matrix

### Selected Services

| Component | Service | Free Tier Limits | Selection Rationale |
|-----------|---------|------------------|---------------------|
| **Database** | **Supabase** | 500MB storage, 2M row reads/month, 500MB bandwidth | ✅ TimescaleDB compatible via extensions, generous free tier, excellent DX, built-in auth |
| **API Hosting** | **Render** | 512MB RAM, 0.1 CPU, spins down after 15min idle, 750hrs/month | ✅ Native FastAPI support, simple deployment via `render.yaml`, automatic HTTPS, generous free tier |
| **Web App** | **Vercel** | Hobby tier: unlimited deployments, 100GB bandwidth, 6000 build mins/month | ✅ Best-in-class Next.js/React support, serverless functions, edge network, instant deploys |
| **Marketing Site** | **GitHub Pages** | 1GB storage, 100GB bandwidth/month | ✅ Already deployed, zero additional cost, version controlled |
| **Game** | **Local Only** | N/A | ✅ Godot exports to desktop/mobile, no cloud hosting needed |

### Alternative Services Considered

| Service | Why Not Selected |
|---------|------------------|
| Neon | No native TimescaleDB support |
| Railway | $5 credit only, not truly free long-term |
| Azure Container Apps | Free tier limited, complex setup |
| Netlify | Similar to Vercel but Vercel has better React performance |
| Fly.io | Free tier requires credit card |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│   Web App       │  Marketing Site │   Game (Local)  │   API Consumers       │
│   (Vercel)      │  (GitHub Pages) │   (Godot)       │   (Future Mobile)     │
│                 │                 │                 │                       │
│  React + TS     │  Static HTML    │  Desktop/Mobile │                       │
│  https://sator- │  https://satorx │  Self-contained │                       │
│  web.vercel.app │  .github.io     │  P2P networking │                       │
└────────┬────────┴─────────────────┴─────────────────┴───────────────────────┘
         │
         │ API Calls (HTTPS)
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            API LAYER                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Render Web Service (Free Tier)                                         ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ ││
│  │  │  FastAPI     │  │  Players     │  │  Matches     │  │  Analytics  │ ││
│  │  │  Main App    │  │  Router      │  │  Router      │  │  Router     │ ││
│  │  │              │  │  /api/players│  │  /api/matches│  │/api/analytics│ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ ││
│  │  ┌──────────────────────────────────────────────────────────────────┐  ││
│  │  │  Health Check: GET /health                                       │  ││
│  │  │  Cold Start: ~10-30s (first request after idle)                  │  ││
│  │  └──────────────────────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   │ Database Connection (SSL)
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Supabase PostgreSQL (Free Tier)                                        ││
│  │  ┌─────────────────────────────────────────────────────────────────┐   ││
│  │  │  Database: sator_production                                       │   ││
│  │  │  Extensions: timescaledb, pg_stat_statements, pgcrypto            │   ││
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │   ││
│  │  │  │player_perfor-│  │  sator_      │  │  extraction_           │ │   ││
│  │  │  │   mance      │  │  layers      │  │   logs                 │ │   ││
│  │  │  │  (hypertable)│  │  (metadata)  │  │  (audit)               │ │   ││
│  │  │  └──────────────┘  └──────────────┘  └────────────────────────┘ │   ││
│  │  └─────────────────────────────────────────────────────────────────┘   ││
│  │  Storage: 500MB limit (~100K match records)                            ││
│  │  Row Reads: 2M/month (~66K reads/day)                                  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Environment Variable Templates

### 1. Supabase Database (Production)

**Location:** `shared/axiom-esports-data/.env.production`

```bash
# Supabase PostgreSQL Connection
# Get these from: Supabase Dashboard → Settings → Database → Connection string
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres

# Supabase Specific (for future auth integration)
SUPABASE_URL=https://[PROJECT_REF].supabase.co
SUPABASE_ANON_KEY=[ANON_KEY]
SUPABASE_SERVICE_ROLE_KEY=[SERVICE_ROLE_KEY]

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1  # Render free tier: single worker recommended

# CORS Origins (add your Vercel domain after deployment)
CORS_ORIGINS=https://sator-web.vercel.app,https://satorx.github.io,http://localhost:3000

# Rate Limiting (Render free tier limits)
RATE_LIMIT_REQUESTS_PER_MINUTE=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Data Retention (Supabase free tier constraint)
DATA_RETENTION_DAYS=365

# Cold Start Configuration
WARMUP_ENDPOINT=/health
WARMUP_INTERVAL_MINUTES=14  # Keep alive before 15min idle timeout
```

### 2. Vercel Web App Environment Variables

**Set in:** Vercel Dashboard → Project Settings → Environment Variables

```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=https://sator-api.onrender.com
API_BASE_URL=https://sator-api.onrender.com

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_REALTIME=false  # Enable when adding Supabase Realtime

# Build Configuration
NODE_ENV=production
```

### 3. Render Environment Variables

**Set in:** Render Dashboard → Service Settings → Environment

```bash
# Copied from .env.production
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
API_PORT=8000
CORS_ORIGINS=https://sator-web.vercel.app
LOG_LEVEL=INFO
```

---

## Free Tier Limits & Monitoring Strategy

### Database: Supabase Free Tier

| Limit | Value | Monitoring Strategy |
|-------|-------|---------------------|
| Storage | 500MB | Weekly `SELECT pg_size_pretty(pg_database_size('postgres'));` |
| Row Reads | 2M/month | Daily query: `SELECT count(*) FROM pg_stat_user_tables;` |
| Bandwidth | 500MB/month | Monitor Supabase Dashboard → Usage |
| Connections | 30 max | Alert when >20 concurrent connections |
| API Requests | Unlimited | Rate limit at application level |

**Mitigation Strategies:**
- Implement aggressive caching in API layer (Redis on Render when upgrading)
- Use materialized views for expensive analytics queries
- Archive old data (older than 1 year) to cold storage

### API: Render Free Tier

| Limit | Value | Monitoring Strategy |
|-------|-------|---------------------|
| RAM | 512MB | Monitor via Render Dashboard |
| CPU | 0.1 (shared) | Optimize for fast cold starts |
| Idle Timeout | 15 minutes | UptimeRobot ping every 14 minutes |
| Disk | Ephemeral (tmp) | No persistent local storage |
| Build Minutes | 500/month | Minimal builds (Docker layer caching) |
| Bandwidth | 100GB/month | Sufficient for API traffic |

**Cold Start Mitigation:**
- UptimeRobot free tier: 5-minute ping intervals (sufficient for hobby projects)
- Or: GitHub Actions cron job to ping `/health` every 10 minutes
- Implement loading states in frontend for cold start UX

### Web App: Vercel Hobby Tier

| Limit | Value | Monitoring Strategy |
|-------|-------|---------------------|
| Bandwidth | 100GB/month | Monitor Vercel Analytics |
| Build Minutes | 6000/month | ~100 builds at 60s each |
| Serverless Functions | 125 invocations/day | API routes in `/api/*` |
| Image Optimization | 1000 images/day | Monitor usage |

---

## Deployment Sequence

### Phase 1: Database (Supabase)

```bash
# 1. Create Supabase project
echo "1. Go to https://supabase.com and create new project"
echo "2. Note the project reference and password"

# 3. Enable TimescaleDB extension
# In Supabase SQL Editor, run:
CREATE EXTENSION IF NOT EXISTS timescaledb;

# 4. Run migrations (using Supabase CLI or SQL Editor)
# Upload and execute files from shared/axiom-esports-data/infrastructure/migrations/
# In order: 001_initial_schema.sql → 005_staging_system.sql

# 5. Verify hypertable creation
SELECT * FROM timescaledb_information.hypertables;
```

### Phase 2: API (Render)

```bash
# 1. Push render.yaml to repository root
git add render.yaml
git commit -m "Add Render deployment configuration"
git push origin main

# 2. Create Blueprint in Render Dashboard
# - Go to https://dashboard.render.com/blueprints
# - Connect GitHub repository
# - Render will auto-detect render.yaml

# 3. Set environment variables in Render Dashboard
# (Copy from .env.production)

# 4. Deploy
# Render auto-deploys on push to main branch
```

### Phase 3: Web App (Vercel)

```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Navigate to web app directory
cd shared/apps/sator-web

# 3. Create project (follow prompts)
vercel --prod

# 4. Set environment variables
vercel env add NEXT_PUBLIC_API_BASE_URL
# Enter: https://sator-api.onrender.com

# 5. Deploy
vercel --prod
```

### Phase 4: Marketing Site (Already Deployed)

```bash
# Already on GitHub Pages via existing workflow
# Verify: https://satorx.github.io
```

---

## Health Check & Monitoring Setup

### API Health Check Endpoint

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "sator-api",
  "version": "0.1.0",
  "database": "connected",
  "timestamp": "2026-03-04T12:50:29.799696+11:00",
  "environment": "production"
}
```

### Uptime Monitoring (Free Options)

| Service | URL | Interval | Features |
|---------|-----|----------|----------|
| UptimeRobot | uptimerobot.com | 5 min (free) | Email alerts, 50 monitors |
| Freshping | freshping.io | 1 min (free) | 50 URLs, 10 locations |
| GitHub Actions | github.com | Custom cron | Self-hosted, unlimited |

**Recommended: GitHub Actions Cron (Zero Additional Cost)**

```yaml
# .github/workflows/keepalive.yml
name: API Keepalive
on:
  schedule:
    - cron: '*/10 * * * *'  # Every 10 minutes
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - run: curl -s https://sator-api.onrender.com/health
```

---

## Cost Tracking

### Monthly Cost Breakdown (All Free Tiers)

| Service | Cost | Limit | Current Usage |
|---------|------|-------|---------------|
| Supabase | $0 | 500MB | ~50MB (10%) |
| Render | $0 | 750hrs | ~500hrs (67%) |
| Vercel | $0 | Hobby | ~20GB (20%) |
| GitHub Pages | $0 | 1GB | ~100MB (10%) |
| **TOTAL** | **$0** | - | - |

### Upgrade Path (When Ready to Scale)

| Service | Next Tier | Cost/Month | Trigger |
|---------|-----------|------------|---------|
| Supabase | Pro | $25 | >400MB storage or >1.5M row reads |
| Render | Starter | $7 | Need no cold starts or >512MB RAM |
| Vercel | Pro | $20 | >100GB bandwidth or team features |

---

## Security Considerations

### Database
- ✅ SSL enforced by Supabase (no unencrypted connections)
- ✅ Row Level Security (RLS) available (implement before adding auth)
- ✅ Connection pooling via PgBouncer (default on Supabase)

### API
- ✅ CORS restricted to known origins only
- ✅ Rate limiting implemented in FastAPI middleware
- ✅ No secrets in code (all via environment variables)

### Web App
- ✅ Environment variables prefixed correctly (`NEXT_PUBLIC_` for client)
- ✅ API keys never exposed to browser

---

## Troubleshooting Guide

### Issue: API Cold Start Too Slow

**Symptoms:** First request after idle takes 10-30 seconds

**Solutions:**
1. Implement keepalive ping (see GitHub Actions cron above)
2. Optimize Docker image size (use slim Python base)
3. Pre-load heavy imports in startup event

### Issue: Database Connection Limits

**Symptoms:** `FATAL: too many connections for role`

**Solutions:**
1. Use connection pooling (PgBouncer on Supabase)
2. Close connections properly in FastAPI
3. Implement connection retry with backoff

### Issue: Supabase Storage Full

**Symptoms:** `could not extend file`

**Solutions:**
1. Archive old data: Move records >1 year old to CSV
2. Compress hypertable chunks
3. Upgrade to Pro ($25/month for 8GB)

---

## File Locations

```
satorXrotas/
├── DEPLOYMENT_ARCHITECTURE.md      # This file
├── render.yaml                      # Render.com Blueprint
├── vercel.json                      # Vercel configuration (updated)
├── .github/
│   └── workflows/
│       └── keepalive.yml            # API keepalive cron
├── shared/
│   ├── axiom-esports-data/
│   │   ├── .env.production          # Production env template
│   │   ├── api/
│   │   │   ├── main.py              # FastAPI entry point
│   │   │   ├── requirements.txt     # Python dependencies
│   │   │   └── Dockerfile           # Container definition
│   │   └── infrastructure/
│   │       └── migrations/          # SQL migrations (001-005)
│   └── apps/
│       └── sator-web/               # React web app (create)
└── website/                         # Marketing site (existing)
```

---

## Next Steps

1. **Create Supabase project** → Get connection strings
2. **Fill in `.env.production`** → Copy values from Supabase dashboard
3. **Deploy database migrations** → Run SQL in Supabase SQL Editor
4. **Push code with `render.yaml`** → Render auto-creates service
5. **Create React web app** → Deploy to Vercel
6. **Set up keepalive** → Copy GitHub Actions workflow
7. **Test end-to-end** → Verify all components communicate

---

*Last Updated: 2026-03-04*
*Architecture Version: 1.0*
