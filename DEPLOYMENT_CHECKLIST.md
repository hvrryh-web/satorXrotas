# SATOR Platform Deployment Checklist

Use this checklist to deploy the SATOR platform step-by-step.

---

## Phase 1: Database (Supabase)

- [ ] **Create Supabase Account**
  - Go to https://supabase.com
  - Sign up with GitHub
  - Create new organization

- [ ] **Create New Project**
  - Project name: `sator-production`
  - Database password: [generate strong password]
  - Region: `US East (N. Virginia)` (closest to Render)
  - Wait for project initialization (~2 minutes)

- [ ] **Get Connection Strings**
  - Go to Settings → Database
  - Copy `URI` connection string
  - Format: `postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres`

- [ ] **Enable TimescaleDB**
  - Go to SQL Editor
  - Run: `CREATE EXTENSION IF NOT EXISTS timescaledb;`
  - Verify: `SELECT * FROM timescaledb_information.hypertables;`

- [ ] **Run Migrations**
  - Go to SQL Editor
  - Run migrations in order:
    1. `shared/axiom-esports-data/infrastructure/migrations/001_initial_schema.sql`
    2. `shared/axiom-esports-data/infrastructure/migrations/002_sator_layers.sql`
    3. `shared/axiom-esports-data/infrastructure/migrations/003_dual_storage.sql`
    4. `shared/axiom-esports-data/infrastructure/migrations/004_extraction_log.sql`
    5. `shared/axiom-esports-data/infrastructure/migrations/005_staging_system.sql`

- [ ] **Verify Database Setup**
  ```sql
  -- Check tables exist
  \dt
  
  -- Check hypertable
  SELECT hypertable_name FROM timescaledb_information.hypertables;
  ```

---

## Phase 2: API (Render)

- [ ] **Commit Configuration Files**
  ```bash
  git add DEPLOYMENT_ARCHITECTURE.md render.yaml shared/axiom-esports-data/api/main.py
  git add shared/axiom-esports-data/api/requirements.txt shared/axiom-esports-data/api/Dockerfile
  git add shared/axiom-esports-data/.env.production
  git commit -m "Add deployment configuration for Render and Supabase"
  git push origin main
  ```

- [ ] **Create Render Account**
  - Go to https://render.com
  - Sign up with GitHub
  - Connect your repository

- [ ] **Deploy via Blueprint**
  - Go to Dashboard → Blueprints
  - Click "New Blueprint Instance"
  - Select your repository
  - Render will detect `render.yaml` and create services

- [ ] **Configure Environment Variables**
  - Go to Dashboard → sator-api → Environment
  - Add `DATABASE_URL` with Supabase connection string
  - Verify other env vars are set from `render.yaml`

- [ ] **Deploy Service**
  - Render will auto-deploy on first creation
  - Monitor build logs for errors
  - Wait for "Your service is live" message

- [ ] **Verify Deployment**
  - Visit `https://sator-api.onrender.com/health`
  - Should return JSON with status: "healthy"

---

## Phase 3: Web App (Vercel)

- [ ] **Navigate to Web App Directory**
  ```bash
  cd shared/apps/sator-web
  ```

- [ ] **Install Vercel CLI (optional)**
  ```bash
  npm i -g vercel
  ```

- [ ] **Create Vercel Project**
  ```bash
  vercel
  # Follow prompts:
  # - Set up and deploy? Yes
  # - Link to existing project? No
  # - What's your project name? sator-web
  ```

- [ ] **Set Environment Variables**
  ```bash
  vercel env add VITE_API_BASE_URL
  # Enter: https://sator-api.onrender.com
  ```

  Or via Dashboard:
  - Go to https://vercel.com/dashboard
  - Select sator-web project
  - Settings → Environment Variables
  - Add `VITE_API_BASE_URL`

- [ ] **Deploy to Production**
  ```bash
  vercel --prod
  ```

- [ ] **Verify Deployment**
  - Visit your Vercel URL
  - Check that API status shows "Online"
  - Navigate to Players page

---

## Phase 4: Keepalive (Prevent Cold Starts)

### Option A: GitHub Actions (Recommended)

- [ ] **Verify Workflow File Exists**
  - Check `.github/workflows/keepalive.yml` is committed

- [ ] **Enable GitHub Actions**
  - Go to repository → Actions tab
  - Click "I understand my workflows, go ahead and enable them"

- [ ] **Verify Cron Job**
  - Workflow runs every 10 minutes automatically
  - Check Actions tab to see runs

### Option B: UptimeRobot (Alternative)

- [ ] **Create UptimeRobot Account**
  - Go to https://uptimerobot.com
  - Sign up for free account

- [ ] **Add Monitor**
  - Monitor Type: HTTP(s)
  - Friendly Name: SATOR API
  - URL: `https://sator-api.onrender.com/health`
  - Monitoring Interval: 5 minutes

- [ ] **Add Alert Contact**
  - Alert Contact Type: Email
  - Enter your email address

---

## Phase 5: Verification & Testing

- [ ] **Health Check**
  ```bash
  curl https://sator-api.onrender.com/health
  ```

- [ ] **API Endpoints**
  ```bash
  # Test players endpoint
  curl https://sator-api.onrender.com/api/players/
  
  # Test with filters
  curl "https://sator-api.onrender.com/api/players/?limit=5&min_maps=50"
  ```

- [ ] **Web App Integration**
  - Open Vercel web app URL
  - Verify Players page loads
  - Test filters and pagination
  - Click on a player to view details

- [ ] **Cold Start Test**
  - Wait 20 minutes without API calls
  - Refresh web app
  - Verify loading banner appears
  - Verify data eventually loads

---

## Phase 6: Documentation & Handoff

- [ ] **Update Marketing Site**
  - Add links to deployed web app
  - Update documentation

- [ ] **Document URLs**
  - API: `https://sator-api.onrender.com`
  - Web App: `https://sator-web.vercel.app` (or your custom domain)
  - Marketing: `https://satorx.github.io`

- [ ] **Share Access**
  - Add team members to Supabase project
  - Add team members to Render service
  - Add team members to Vercel project

---

## Post-Deployment Monitoring

### Weekly Checks

- [ ] Check Supabase usage dashboard
  - Storage: Keep under 400MB (80% of 500MB limit)
  - Row reads: Keep under 1.5M (75% of 2M limit)

- [ ] Check Render usage
  - Hours: Keep under 700 (93% of 750hr limit)

- [ ] Check Vercel usage
  - Bandwidth: Keep under 80GB (80% of 100GB limit)

### Monthly Maintenance

- [ ] Review error logs in Render Dashboard
- [ ] Check for dependency updates
- [ ] Verify backups are working
- [ ] Review analytics and user feedback

---

## Troubleshooting

### API Returns 503 / "Service Unavailable"

1. Check Render Dashboard → Logs
2. Verify DATABASE_URL is correct
3. Test database connection from local machine

### Database Connection Errors

1. Verify Supabase project is active
2. Check connection string format
3. Ensure IP allowlist includes Render IPs (0.0.0.0/0 for free tier)

### Web App Shows "Offline"

1. Check CORS_ORIGINS in Render env vars includes Vercel domain
2. Verify API is healthy via `/health` endpoint
3. Check browser console for CORS errors

### Cold Starts Too Slow

1. Verify keepalive workflow is running (check Actions tab)
2. Check that cron schedule is `*/10 * * * *`
3. Consider upgrading to Render Starter ($7/month) for no cold starts

---

## Upgrade Path

When ready to scale:

| Current | Upgrade To | Cost | When to Upgrade |
|---------|-----------|------|-----------------|
| Supabase Free | Pro | $25/mo | >400MB storage |
| Render Free | Starter | $7/mo | Cold starts problematic |
| Vercel Hobby | Pro | $20/mo | >100GB bandwidth |

---

*Last Updated: 2026-03-04*
