# @njz-os/site

NJZ RAT-OS marketing site. Next.js 15 App Router, SSG/ISR-first.

## Develop

```bash
pnpm --filter @njz-os/site dev
# → http://localhost:3000
```

## Build

```bash
pnpm --filter @njz-os/site build
pnpm --filter @njz-os/site start
```

## Routes (Phase 0 placeholder)

- `/` — landing
- `/pricing` — pricing page (Phase 1)
- `/modules/*` — per-module previews (Phase 1)
- `/about` — team / mission (Phase 1)
- `/blog` — content marketing (Phase 2+)

## Deployment

Vercel. Config in `infra/vercel/site.json`. Auto-deploys from `main`; preview deploys on every PR.
