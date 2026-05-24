# @njz-os/web

NJZ RAT-OS webapp. Vite + React 19 SPA. Hosts the seven product modules + PolyCo.World.

## Develop

```bash
pnpm --filter @njz-os/web dev
# → http://localhost:5173
```

## Build

```bash
pnpm --filter @njz-os/web build
pnpm --filter @njz-os/web preview
```

## Routes (Phase 0)

All module routes render a Phase Stub placeholder. Implementation lands per phase gates.

| Route | Module | Gate | Phase |
|-------|--------|------|-------|
| `/` | Home | — | — |
| `/focus` | Focus Hero | `G1.focus-hero` | 1 |
| `/sound` | Soundscapes | `G1.soundscapes` | 1 |
| `/blocker` | Distraction Blocker | `G1.blocker` | 1 |
| `/world` | PolyCo.World | `G1.polyworld-office` | 1 |
| `/train` | Brain Training | `G2.brain-training` | 2 |
| `/write` | Writing Space | `G2.writing-space` | 2 |
| `/learn` | Micro-Learning | `G2.micro-learning` | 2 |

## Phase Gates

`src/shared/gates.ts` knows current gate status. Enable `VITE_STRICT_GATES=true` in CI to fail builds that touch locked modules.

## Deployment

Vercel. Config in `infra/vercel/web.json`.
