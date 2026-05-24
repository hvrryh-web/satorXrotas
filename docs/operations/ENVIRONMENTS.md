[Ver001.000]

# Environments — NJZ RAT-OS

## Environment Variables

### Client-exposed (Next.js — `apps/site`)

```
NEXT_PUBLIC_APP_ENV=local|preview|staging|production
NEXT_PUBLIC_API_URL=https://api.staging.njz-rat-os.app
NEXT_PUBLIC_VAULTBRAIN_WS_URL=wss://vaultbrain.staging.njz.app
NEXT_PUBLIC_SITE_URL=https://staging.njz-rat-os.app
```

### Client-exposed (Vite — `apps/web`)

```
VITE_APP_ENV=local|preview|staging|production
VITE_API_URL=https://api.staging.njz-rat-os.app
VITE_WS_URL=wss://vaultbrain.staging.njz.app
VITE_AGENT_GATEWAY_URL=https://agent.staging.njz.app
VITE_IDENTITY_URL=https://identity.staging.njz.app
```

### Server-only (`services/rat-os-api`, Phase 2+)

```
NODE_ENV=production
VAULTBRAIN_API_URL=https://vaultbrain.staging.njz.app
VAULTBRAIN_SHARED_SECRET=<secret>
AGENT_GATEWAY_API_KEY=<secret>
IDENTITY_JWKS_URL=https://identity.staging.njz.app/.well-known/jwks.json
SENTRY_DSN=<optional>
```

## Local Setup

```bash
# Clone
git clone https://github.com/hvrryh-web/satorXrotas.git
cd satorXrotas

# Install
pnpm install

# Env
cp .env.example .env.local
# Edit .env.local with local values (vaultbrain via upstream's docker-compose or stub)

# Dev
pnpm dev
```

## Stub Backend For Local Dev

If you don't want to run the upstream services locally, use the stub:

```bash
pnpm --filter @njz-os/adapters-vaultbrain-client dev:stub
# Starts a local stub on :7100 mimicking vaultbrain's WS + HTTP surface
```

Set `VITE_API_URL=http://localhost:7100` and `VITE_WS_URL=ws://localhost:7100/ws`.

## Docker Compose (Phase 2+)

`infra/docker/docker-compose.yml` will compose:

- Postgres 15 (for `services/rat-os-api` BFF cache, if needed)
- Redis 7 (for session cache, queue)
- Localstack (optional, for S3-compatible asset dev)

Upstream ZeSporteXte ships its own compose for vaultbrain + agent-gateway + identity. Run their compose alongside ours for full local parity.

## Health Endpoints

| Service | Path |
|---------|------|
| `apps/site` | `/api/health` |
| `apps/web` | `/health.json` (static) |
| `services/rat-os-api` (Phase 2+) | `/health` |

Returns 200 with JSON `{ version, commit, env, dependencies: {...} }`.

## Secrets Management

- Local: `.env.local` (gitignored).
- Vercel: project env settings, marked "Sensitive" for server-only vars.
- Render: service env settings.
- Rotation policy: every 90 days minimum. Documented in `SECURITY.md`.

## Naming Domains (TBD)

Pending decision:

| Surface | Candidate |
|---------|-----------|
| Marketing site | `njz-rat-os.app` or `ratos.njz.app` |
| Webapp | same domain, `/app` path, or `app.njz-rat-os.app` |
| API | `api.njz-rat-os.app` |

Decision in ADR (TBD) before Phase 1 launch.
