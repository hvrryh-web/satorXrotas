[Ver001.000]

# Deployment — NJZ RAT-OS

> Phase 0 documents *intent*. No production deploys yet. Phase 1 ships the first production environment.

## Surface → Host

| Surface | Host | Branch trigger | Runtime |
|---------|------|----------------|---------|
| `apps/site` | Vercel | `main` (prod), PR (preview) | Node 20 + Edge |
| `apps/web` | Vercel | `main` (prod), PR (preview) | Static + SPA |
| `services/rat-os-api` (Phase 2+) | Render | tagged release | Node 20 server |
| `apps/desktop-widget` (Phase 2+) | GitHub Releases (binary) | tagged release | Tauri |

## Environments

| Env | Domain (TBD) | Purpose |
|-----|--------------|---------|
| Local | `localhost:3000` (site), `localhost:5173` (web) | Dev |
| Preview | `pr-<n>.njz-rat-os.vercel.app` | Per-PR |
| Staging | `staging.njz-rat-os.app` | Pre-prod integration with ZeSporteXte staging |
| Production | `njz-rat-os.app` | Live |

## CI → Deploy Flow

```
PR open       →  CI: lint + typecheck + unit + e2e smoke   →  Vercel preview deploy
PR merge      →  CI: full test suite                       →  Vercel prod deploy
Release tag   →  CI: full + e2e + perf                     →  Render deploy (services)
                                                              → CHANGELOG.md auto-update
                                                              → Release notes posted
```

## Vercel Configuration

`infra/vercel/site.json` and `infra/vercel/web.json` hold the per-app config. Key settings:

- Framework preset: `nextjs` (site), `vite` (web).
- Build command: `pnpm turbo run build --filter=<app>`.
- Output dir: `.next/` (site) or `dist/` (web).
- Env: from Vercel project settings; templates in `.env.example`.

## Render Configuration (Phase 2+)

`infra/render/render.yaml` defines the `rat-os-api` service. Auto-deploy on tagged releases only — never on `main` pushes.

## Environment Variables

Templates in `.env.example`. Real values in Vercel / Render project settings. Never commit real values.

Categories:

- `NEXT_PUBLIC_*` / `VITE_*` — exposed to client; safe for marketing copy, public IDs.
- Server-only — vaultbrain URL, API keys, auth secrets. Never in `NEXT_PUBLIC_*`.

See `ENVIRONMENTS.md` for the full variable inventory.

## Rollback

- Vercel: instant rollback via dashboard ("Promote previous deployment").
- Render: revert to previous release tag; redeploy.
- Database migrations (Phase 2+): reversible migrations only; never destructive on first apply.

## Smoke Tests Post-Deploy

`scripts/smoke-prod.sh` (TBD) runs against the production URL:

- `/` returns 200.
- `/api/health` returns 200 with version + commit SHA.
- WebSocket connect to vaultbrain succeeds (smoke account).

## Deploy Permissions

| Role | Local | Preview | Staging | Production |
|------|-------|---------|---------|------------|
| Any contributor | ✓ | ✓ (auto from PR) | ✗ | ✗ |
| Maintainer | ✓ | ✓ | ✓ | ✓ |
| Agent | ✓ | ✓ (auto from PR) | ✗ | ✗ |

Agents do not deploy to staging or production. They open PRs; maintainers approve and merge; CI deploys.
