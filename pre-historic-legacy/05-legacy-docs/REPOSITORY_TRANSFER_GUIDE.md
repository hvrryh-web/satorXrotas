# Repository Transfer Guide

**Source:** `satorXrotas` (Local/Git)  
**Target:** New GitHub Repository  
**Version:** 1.0.0  
**Date:** 2026-03-04  

---

## Table of Contents

1. [Pre-Transfer Checklist](#pre-transfer-checklist)
2. [Transfer Process](#transfer-process)
3. [Free-Tier Technologies](#free-tier-technologies)
4. [Risk Assessment](#risk-assessment)
5. [Cost Mitigation](#cost-mitigation)
6. [Post-Transfer Verification](#post-transfer-verification)
7. [Troubleshooting](#troubleshooting)

---

## Pre-Transfer Checklist

### Code Repository Preparation

- [ ] **Clean Working Directory**
  ```bash
  git status
  # Should show no uncommitted changes
  ```

- [ ] **Backup Current State**
  ```bash
  git bundle create sator-backup-$(date +%Y%m%d).bundle --all
  ```

- [ ] **Audit Sensitive Files**
  ```bash
  # Check for secrets
  git log --all --full-history -- .env
  git log --all --full-history -- '*password*'
  git log --all --full-history -- '*secret*'
  git log --all --full-history -- '*key*'
  ```

- [ ] **Sanitize History (if needed)**
  ```bash
  # Remove sensitive data from history
  git filter-branch --force --index-filter \
    'git rm --cached --ignore-unmatch path/to/sensitive-file' \
    --prune-empty --tag-name-filter cat -- --all
  ```

- [ ] **Verify Large Files**
  ```bash
  # Find files >10MB
  find . -type f -size +10M -not -path './.git/*'
  
  # Check git LFS status
  git lfs status
  ```

### Documentation Review

- [ ] All documentation files updated:
  - [ ] `README.md`
  - [ ] `ARCHITECTURE.md`
  - [ ] `CHANGELOG.md`
  - [ ] `DESIGN_OVERVIEW.md`
  - [ ] `DESIGN_GAP_ANALYSIS.md`
  - [ ] `CRIT_REPORT.md`
  - [ ] `DEPLOYMENT_ARCHITECTURE.md`
  - [ ] `DEPLOYMENT_CHECKLIST.md`
  - [ ] `AGENTS.md`

- [ ] License files verified
- [ ] Contributing guidelines present
- [ ] Code of conduct added

### Environment Files Preparation

- [ ] **Create `.env.example` files**
  ```bash
  # Verify these exist and are complete:
  shared/axiom-esports-data/.env.example
  shared/axiom-esports-data/api/.env.example
  shared/axiom-esports-data/infrastructure/.env.example
  shared/apps/sator-web/.env.example
  ```

- [ ] **Verify `.gitignore`**
  ```bash
  # Should exclude:
  .env
  .env.local
  .env.production
  node_modules/
  __pycache__/
  *.pyc
  .venv/
  dist/
  build/
  .godot/
  *.tmp
  ```

---

## Transfer Process

### Step 1: Create New GitHub Repository

1. **Navigate to GitHub**
   - Go to https://github.com/new
   - Repository name: `sator-platform` (or preferred)
   - Visibility: Public or Private
   - **DO NOT** initialize with README (will use existing)

2. **Note the Repository URL**
   ```
   https://github.com/YOUR_USERNAME/sator-platform.git
   ```

### Step 2: Prepare Local Repository

```bash
# Navigate to repository
cd /path/to/satorXrotas

# Verify clean state
git status

# Fetch all remote references
git fetch --all

# Create a backup branch
git branch backup-pre-transfer

# List all branches
git branch -a
```

### Step 3: Update Remote URLs

```bash
# Add new remote
 git remote add github https://github.com/YOUR_USERNAME/sator-platform.git

# Verify remotes
git remote -v
# Should show:
# origin    https://github.com/original/repo.git (fetch)
# origin    https://github.com/original/repo.git (push)
# github    https://github.com/YOUR_USERNAME/sator-platform.git (fetch)
# github    https://github.com/YOUR_USERNAME/sator-platform.git (push)
```

### Step 4: Push All Branches and Tags

```bash
# Push all branches
 git push github --all

# Push all tags
 git push github --tags

# Push specific branches if needed
 git push github main
 git push github develop
```

### Step 5: Transfer Git LFS Objects (if applicable)

```bash
# Check if LFS is used
git lfs ls-files

# If files exist, push LFS objects
 git lfs push github --all
```

### Step 6: Configure New Repository Settings

1. **Branch Protection Rules**
   - Go to Settings > Branches
   - Add rule for `main`:
     - Require pull request reviews
     - Require status checks
     - Require up-to-date branches
     - Include administrators

2. **Environment Secrets**
   - Go to Settings > Secrets and variables > Actions
   - Add the following secrets:

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `DATABASE_URL` | Supabase PostgreSQL URL | ✅ Yes |
| `SUPABASE_URL` | Supabase project URL | ✅ Yes |
| `SUPABASE_KEY` | Supabase service key | ✅ Yes |
| `RENDER_API_KEY` | Render deployment key | ✅ Yes |
| `VERCEL_TOKEN` | Vercel deployment token | ✅ Yes |
| `SLACK_WEBHOOK_URL` | Alert notifications | ⚠️ Recommended |
| `SENTRY_DSN` | Error tracking | ⚠️ Recommended |

3. **Repository Variables**
   - Go to Settings > Secrets and variables > Variables
   - Add:

| Variable Name | Value | Description |
|---------------|-------|-------------|
| `RENDER_SERVICE_ID` | `srv_xxxx` | Render service ID |
| `VERCEL_ORG_ID` | `team_xxxx` | Vercel organization |
| `VERCEL_PROJECT_ID` | `prj_xxxx` | Vercel project ID |

4. **Disable Unused Features**
   - Settings > Options:
     - [ ] Wikis (unless needed)
     - [ ] Issues (enable)
     - [ ] Projects (enable)
     - [ ] Discussions (disable)

### Step 7: Update Repository References

```bash
# Update origin to point to new repo (optional)
 git remote set-url origin https://github.com/YOUR_USERNAME/sator-platform.git

# Remove old remote
 git remote remove origin-old

# Verify
git remote -v
```

### Step 8: Verify Transfer

```bash
# Clone fresh copy
cd /tmp
git clone https://github.com/YOUR_USERNAME/sator-platform.git sator-verify

# Verify all files present
cd sator-verify
find . -type f | wc -l

# Check branch history
git log --oneline -20

# Verify LFS files (if applicable)
git lfs ls-files
```

---

## Free-Tier Technologies

### Infrastructure Stack

| Component | Service | Free Tier Limits | Usage Estimate |
|-----------|---------|------------------|----------------|
| **Database** | Supabase | 500MB storage, 2M reads/month | ~200MB, 500k reads |
| **API Hosting** | Render | 512MB RAM, 750hrs/month | Within limits |
| **Web Hosting** | Vercel | 100GB bandwidth/month | ~20GB |
| **Static Site** | GitHub Pages | 1GB storage, 100GB bandwidth | ~500MB |
| **CI/CD** | GitHub Actions | 2000 mins/month | ~500 mins |
| **Secrets** | GitHub Secrets | 100 secrets/repo | ~20 secrets |
| **Monitoring** | UptimeRobot | 50 monitors, 5min interval | 10 monitors |

### Third-Party Services (Free Tier)

| Service | Purpose | Free Tier | Risk Level |
|---------|---------|-----------|------------|
| **Sentry** | Error Tracking | 5k errors/month | 🟢 Low |
| **Upstash** | Redis Caching | 10k requests/day | 🟡 Medium |
| **Logtail** | Log Aggregation | 100MB/month | 🟢 Low |
| **Plausible** | Analytics | 10k pageviews | 🟢 Low |

### Development Tools (Free)

| Tool | Purpose | License |
|------|---------|---------|
| Godot 4.x | Game Engine | MIT |
| VS Code | IDE | MIT |
| PostgreSQL 15 | Database | PostgreSQL |
| Docker Desktop | Containerization | Free for small teams |
| Postman | API Testing | Free tier |
| Figma | Design | Free tier |

---

## Risk Assessment

### High-Risk Areas

#### R-1: Secret Exposure During Transfer
**Risk:** Sensitive credentials may be exposed in history  
**Impact:** 🔴 CRITICAL  
**Likelihood:** MEDIUM  

**Mitigation:**
1. Run secret scanner before transfer:
   ```bash
   # Install git-secrets
   git secrets --scan-history
   
   # Or use truffleHog
   truffleHog git file://.
   ```

2. Rotate all credentials after transfer:
   - Supabase database password
   - Render API key
   - Vercel token
   - Any third-party API keys

3. Verify no secrets in code:
   ```bash
   grep -r "sk-" . --include="*.py" --include="*.ts" --include="*.js"
   grep -r "password" . --include="*.py" --include="*.ts"
   ```

**Post-Transfer Action:**
- [ ] Rotate all credentials
- [ ] Update GitHub Secrets
- [ ] Test all services

---

#### R-2: CI/CD Pipeline Failure
**Risk:** GitHub Actions may fail on new repository  
**Impact:** 🟠 HIGH  
**Likelihood:** MEDIUM  

**Mitigation:**
1. **Test workflows before go-live:**
   ```bash
   # Install act for local testing
   act push
   act pull_request
   ```

2. **Common failure points:**
   - Missing secrets
   - Incorrect repository references
   - Path issues
   - Permission errors

3. **Verify workflow files:**
   ```yaml
   # Check all workflows reference correct paths
   # .github/workflows/*.yml
   ```

**Post-Transfer Action:**
- [ ] Trigger test workflow
- [ ] Verify all secrets accessible
- [ ] Check artifact uploads

---

#### R-3: Cold Start Performance Degradation
**Risk:** Free-tier services may have cold start delays  
**Impact:** 🟡 MEDIUM  
**Likelihood:** HIGH  

**Mitigation:**
1. **Keepalive Configuration:**
   ```yaml
   # .github/workflows/keepalive.yml
   # Already configured to ping every 10 minutes
   ```

2. **Connection Pooling:**
   ```python
   # FastAPI - already configured
   pool_size=2
   max_overflow=3
   ```

3. **Health Check Endpoints:**
   ```
   GET /health - Basic health
   GET /ready - Ready for traffic
   GET /live - Liveness probe
   ```

**Cost Impact:** None (keepalive is free)  
**Post-Transfer Action:**
- [ ] Verify keepalive workflow runs
- [ ] Test cold start times
- [ ] Monitor response times

---

#### R-4: Database Connection Limits
**Risk:** Supabase free tier has connection limits  
**Impact:** 🟠 HIGH  
**Likelihood:** MEDIUM  

**Supabase Limits:**
- Free tier: 60 concurrent connections
- Connection pooler: 200 connections

**Mitigation:**
1. **Use Connection Pooler (port 6543):**
   ```
   postgresql://user:pass@host:6543/postgres?sslmode=require
   ```

2. **Connection Pooling in Application:**
   ```python
   # Already configured in api/src/db.py
   pool_size = 2
   max_overflow = 3
   pool_timeout = 30
   ```

3. **Monitor Connection Usage:**
   ```sql
   -- In Supabase SQL Editor
   SELECT count(*) FROM pg_stat_activity;
   ```

**Cost Impact:** If exceeded, may need Supabase Pro ($25/mo)  
**Post-Transfer Action:**
- [ ] Monitor connection count
- [ ] Verify pooler configuration
- [ ] Set up connection alerts

---

#### R-5: Render Free Tier Limitations
**Risk:** Render free tier spins down after 15 min idle  
**Impact:** 🟡 MEDIUM  
**Likelihood:** CERTAIN  

**Limitations:**
- 512MB RAM
- Sleeps after 15 min idle
- Limited to 750hrs/month
- No custom domains on free tier

**Mitigation:**
1. **Keepalive Script (already implemented):**
   ```yaml
   # .github/workflows/keepalive.yml
   schedule:
     - cron: '*/10 * * * *'  # Every 10 minutes
   ```

2. **Upgrade Path:**
   - Render Starter: $7/month (always on)
   - Required if: >750hrs usage or sleep unacceptable

**Cost Impact:** $0 (with keepalive) or $7/month  
**Post-Transfer Action:**
- [ ] Verify keepalive works
- [ ] Monitor usage hours
- [ ] Plan upgrade if needed

---

#### R-6: Vercel Function Limitations
**Risk:** Serverless function cold starts and limits  
**Impact:** 🟡 MEDIUM  
**Likelihood:** MEDIUM  

**Limits:**
- 100GB bandwidth/month
- 10s function timeout (Hobby)
- 1024MB memory (Hobby)

**Mitigation:**
1. **Static Generation:**
   - Pre-render pages where possible
   - Use ISR (Incremental Static Regeneration)

2. **Edge Functions:**
   - Move simple logic to edge
   - Lower latency, no cold start

3. **Monitoring:**
   ```bash
   # Vercel CLI
   vercel logs --json
   ```

**Cost Impact:** Vercel Pro ($20/mo) if exceeded  
**Post-Transfer Action:**
- [ ] Monitor bandwidth usage
- [ ] Review function logs
- [ ] Optimize if needed

---

#### R-7: GitHub Actions Minute Limits
**Risk:** Exceeding 2000 free minutes/month  
**Impact:** 🟡 MEDIUM  
**Likelihood:** LOW  

**Current Usage Estimate:**
- Build/test: ~5 min per run
- Keepalive: ~1 min per run (432 runs/month)
- Total: ~450 min/month

**Mitigation:**
1. **Optimize Workflows:**
   ```yaml
   # Use caching
   - uses: actions/cache@v3
     with:
       path: ~/.npm
       key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
   ```

2. **Conditional Runs:**
   ```yaml
   on:
     push:
       paths-ignore:
         - '**.md'
         - 'docs/**'
   ```

**Cost Impact:** $0.008/minute after free tier  
**Post-Transfer Action:**
- [ ] Monitor Actions usage
- [ ] Optimize if approaching limit

---

## Cost Mitigation

### Free-Tier Optimization Strategies

#### 1. Database Cost Control

| Strategy | Implementation | Savings |
|----------|---------------|---------|
| **Compression** | TimescaleDB auto-compression (30 days) | 70% storage |
| **Archival** | Move old data to S3 after 1 year | $0 cold storage |
| **Indexing** | Proper indexes reduce read ops | 50% read reduction |
| **Caching** | Redis for frequent queries | 80% DB load reduction |

**Implementation:**
```sql
-- Enable compression (already in migrations)
ALTER TABLE matches_cs SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'team_id'
);

SELECT add_compression_policy('matches_cs', INTERVAL '30 days');
```

---

#### 2. API Cost Control

| Strategy | Implementation | Savings |
|----------|---------------|---------|
| **Connection Pooling** | Reuse connections | 60% connection reduction |
| **Caching** | Redis for API responses | 70% compute reduction |
| **Batch Requests** | Combine multiple queries | 50% request reduction |
| **Lazy Loading** | Only fetch required data | 40% bandwidth reduction |

**Implementation:**
```python
# FastAPI caching middleware
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@app.get("/api/players")
@cache(expire=300)  # 5 min cache
async def get_players():
    return await db.get_players()
```

---

#### 3. Web Cost Control

| Strategy | Implementation | Savings |
|----------|---------------|---------|
| **Image Optimization** | WebP format, srcset | 60% bandwidth |
| **Code Splitting** | Lazy load routes | 40% initial load |
| **Static Export** | Pre-render where possible | 80% function calls |
| **CDN Caching** | Aggressive cache headers | 90% origin requests |

**Implementation:**
```typescript
// Lazy load heavy components
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'));

// Image optimization
<img src="image.webp" 
     srcSet="image-400.webp 400w, image-800.webp 800w"
     loading="lazy" />
```

---

#### 4. Pipeline Cost Control

| Strategy | Implementation | Savings |
|----------|---------------|---------|
| **Selective Extraction** | Only changed data | 70% extraction time |
| **Batch Inserts** | 100 rows per transaction | 80% DB writes |
| **Rate Limiting** | Respect source limits | Avoid bans |
| **Caching** | Cache external API calls | 60% external requests |

**Implementation:**
```python
# Batch inserts
await conn.copy_records_to_table(
    'matches',
    records=batch_data
)
```

---

### Cost Monitoring Dashboard

Create a simple cost tracking spreadsheet:

| Service | Free Limit | Current | Projected | Action |
|---------|-----------|---------|-----------|--------|
| Supabase Storage | 500MB | 200MB | 400MB | ✅ OK |
| Supabase Reads | 2M/month | 500k | 1.5M | ✅ OK |
| Render Hours | 750/mo | 720 | 720 | ⚠️ Watch |
| Vercel Bandwidth | 100GB | 20GB | 50GB | ✅ OK |
| GitHub Actions | 2000min | 450 | 600 | ✅ OK |

---

### Upgrade Decision Matrix

| When to Upgrade | From | To | Cost |
|-----------------|------|-----|------|
| Database >400MB | Supabase Free | Pro ($25/mo) | $25/mo |
| Render sleeps causing issues | Free | Starter ($7/mo) | $7/mo |
| Vercel >80GB bandwidth | Hobby | Pro ($20/mo) | $20/mo |
| GitHub >1900min | Free | Team ($4/mo) | $4/mo |
| **Total if all needed** | | | **$56/mo** |

---

## Post-Transfer Verification

### Phase 1: Repository Integrity (Immediate)

- [ ] Clone repository fresh
- [ ] Verify all branches present
- [ ] Verify all tags present
- [ ] Check file count matches
- [ ] Verify git history intact

```bash
# Verification commands
git clone https://github.com/YOUR_USERNAME/sator-platform.git
cd sator-platform
git log --oneline -5
git branch -a
git tag -l
find . -type f -not -path './.git/*' | wc -l
```

### Phase 2: Secret Configuration (Day 1)

- [ ] Add DATABASE_URL to GitHub Secrets
- [ ] Add SUPABASE_URL to GitHub Secrets
- [ ] Add SUPABASE_KEY to GitHub Secrets
- [ ] Add RENDER_API_KEY to GitHub Secrets
- [ ] Add VERCEL_TOKEN to GitHub Secrets
- [ ] Add SLACK_WEBHOOK_URL (optional)
- [ ] Add SENTRY_DSN (optional)

### Phase 3: Database Setup (Day 1-2)

- [ ] Create Supabase project
- [ ] Run migrations 001-009
- [ ] Seed initial data
- [ ] Verify connection from local
- [ ] Test connection pooling

```bash
# Run migrations
cd shared/axiom-esports-data/infrastructure
psql $DATABASE_URL -f migrations/001_initial_schema.sql
# ... repeat for all migrations

# Verify
psql $DATABASE_URL -c "\dt"
```

### Phase 4: API Deployment (Day 2-3)

- [ ] Connect Render to new GitHub repo
- [ ] Configure environment variables
- [ ] Deploy API
- [ ] Verify health endpoints
- [ ] Test firewall middleware

```bash
# Test health
curl https://your-api.onrender.com/health
curl https://your-api.onrender.com/ready
curl https://your-api.onrender.com/live
```

### Phase 5: Web Deployment (Day 3-4)

- [ ] Connect Vercel to new GitHub repo
- [ ] Configure build settings
- [ ] Set environment variables
- [ ] Deploy web app
- [ ] Verify all pages load

```bash
# Run locally first
cd shared/apps/sator-web
npm install
npm run build
npm run preview
```

### Phase 6: Pipeline Setup (Day 4-5)

- [ ] Configure GitHub Actions
- [ ] Test keepalive workflow
- [ ] Test extraction workflow
- [ ] Verify job coordinator starts
- [ ] Test agent workers

```bash
# Trigger manually
gh workflow run keepalive.yml
gh workflow run extraction.yml
```

### Phase 7: Monitoring Setup (Day 5-7)

- [ ] Set up UptimeRobot monitors
- [ ] Configure Sentry project
- [ ] Set up log aggregation
- [ ] Test alert channels
- [ ] Create status page

### Phase 8: End-to-End Testing (Day 7)

- [ ] Test complete user flow
- [ ] Verify data extraction
- [ ] Check data visualization
- [ ] Test error scenarios
- [ ] Performance baseline

---

## Verification Checklist

### Pre-Transfer
- [ ] Clean git status
- [ ] Backup created
- [ ] Secrets audited
- [ ] Documentation complete
- [ ] .env.example files present
- [ ] .gitignore properly configured

### During Transfer
- [ ] New GitHub repo created
- [ ] All branches pushed
- [ ] All tags pushed
- [ ] LFS objects transferred
- [ ] Remote URLs updated

### Post-Transfer
- [ ] Repository clones successfully
- [ ] All files present
- [ ] Git history intact
- [ ] GitHub Secrets configured
- [ ] Branch protection enabled
- [ ] Workflows functional
- [ ] Database migrations run
- [ ] API deployed and healthy
- [ ] Web app deployed and functional
- [ ] Pipeline operational
- [ ] Monitoring active
- [ ] Alerts configured

### Cost Verification
- [ ] Supabase within limits
- [ ] Render within limits
- [ ] Vercel within limits
- [ ] GitHub Actions within limits
- [ ] No unexpected charges

---

## Troubleshooting

### Issue: Push Rejected - Large Files

**Solution:**
```bash
# Use Git LFS
git lfs track "*.psd"
git lfs track "*.mp4"
git add .gitattributes
git commit -m "Track large files with LFS"
git push github main
```

### Issue: Secrets Not Accessible

**Solution:**
```bash
# Verify secret name matches exactly
echo ${{ secrets.DATABASE_URL }} | head -c 10

# Check repository settings
# Settings > Secrets and variables > Actions
```

### Issue: CI/CD Fails on New Repo

**Solution:**
```bash
# Check workflow logs
gitHub.com/YOUR_USERNAME/sator-platform/actions

# Common fixes:
# 1. Re-add secrets
# 2. Update repository references in workflows
# 3. Check file paths
```

### Issue: Database Connection Fails

**Solution:**
```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Verify:
# 1. Connection string format
# 2. IP allowlist in Supabase
# 3. Using pooler port 6543
# 4. SSL mode enabled
```

### Issue: Cold Starts Too Slow

**Solution:**
```bash
# Verify keepalive is running
# Check GitHub Actions logs for keepalive workflow

# If still slow, consider:
# 1. Upgrading Render to Starter ($7/mo)
# 2. Implementing edge caching
# 3. Using Vercel Edge Functions
```

---

## Contact & Support

For issues during transfer:

1. **GitHub Support:** https://support.github.com
2. **Supabase Support:** https://supabase.com/support
3. **Render Support:** https://render.com/docs
4. **Vercel Support:** https://vercel.com/support

---

## Appendix A: Transfer Commands Quick Reference

```bash
# Complete transfer sequence
cd /path/to/satorXrotas

# 1. Backup
git bundle create backup-$(date +%Y%m%d).bundle --all

# 2. Add new remote
 git remote add github https://github.com/YOUR_USERNAME/sator-platform.git

# 3. Push everything
 git push github --all
 git push github --tags

# 4. Verify
git ls-remote github

# 5. Update origin (optional)
 git remote set-url origin https://github.com/YOUR_USERNAME/sator-platform.git
```

---

## Appendix B: Environment Variables Template

Create this file locally (DO NOT COMMIT):

```bash
# .env.transfer
# Fill in and add to GitHub Secrets

# Database
DATABASE_URL=postgresql://postgres:PASSWORD@HOST:6543/postgres?sslmode=require
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...

# Deployment
RENDER_API_KEY=rnd_...
VERCEL_TOKEN=...
VERCEL_ORG_ID=team_...
VERCEL_PROJECT_ID=prj_...

# Monitoring
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
SENTRY_DSN=https://...@....ingest.sentry.io/...
UPTIMEROBOT_API_KEY=ur...
```

---

*This guide ensures a safe, complete transfer of the SATOR platform repository to GitHub with zero-cost deployment and comprehensive risk mitigation.*
