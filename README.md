# NJZ RAT-OS

> **Your Neural Operating System** — a unified wellness-productivity platform.
> Train. Focus. Create. Learn. Grow.

NJZ **RAT-OS** is the consumer-facing brand for **NJZ-OS** (Neural Operating System), a cross-platform wellness-productivity OS that integrates Focus Training, Soundscapes, Distraction Blocking, Writing Space, Micro-Learning, Brain Training, and the **PolyCo.World** pixel-art metaverse into one cohesive experience.

This repository is the **monorepo** for the RAT-OS marketing site and webapp. It consumes shared services and packages from [`notbleaux/ZeSporteXte`](https://github.com/notbleaux/ZeSporteXte) (the NJZ platform monorepo) via the `@njz/*` npm scope.

---

## Repository Identity

| Field | Value |
|-------|-------|
| Marketing brand | **NJZ RAT-OS** |
| Technical platform | NJZ-OS |
| Package scopes | `@njz/*` (upstream, ZeSporteXte) · `@njz-os/*` (this repo) |
| Repo role | RAT-OS site + webapp monorepo |
| Upstream platform | [`notbleaux/ZeSporteXte`](https://github.com/notbleaux/ZeSporteXte) |
| Build system | pnpm workspaces + Turborepo |
| Primary languages | TypeScript, React, Next.js |
| AI framework | NJZPOF v0.2 (see `.agents/`, `ROOT_AXIOMS/`) |

---

## Quick Start

```bash
# Prerequisites
node --version   # 20.x
pnpm --version   # 9.x

# Install
pnpm install

# Develop
pnpm dev:site    # Marketing site (Next.js) on :3000
pnpm dev:web     # Webapp (Vite + React) on :5173

# Quality
pnpm typecheck
pnpm lint
pnpm test

# Build
pnpm build
```

See `docs/operations/DEPLOYMENT.md` for production deployment.

---

## Monorepo Layout

```
apps/
  site/               # Marketing site (Next.js 15, App Router)
  web/                # Main webapp (Vite + React 19, 7 modules)
  desktop-widget/     # Tauri shell (Phase 2)
  pwa-shell/          # PWA wrapper

packages/
  @njz-os/
    core/             # Domain types
    ui/               # Design system + tokens
    audio-engine/     # Soundscapes + binaural beats
    focus-engine/     # Timer + session state machines
    polyworld/        # PolyCo.World rendering
    pixel-art/        # Pixel-art helpers
    progression/      # XP / streaks / rewards
    analytics/        # Cognitive profile + scoring
    learning-cards/   # Micro-learning data model
    writing/          # Editor + manuscript model
    tsconfig/         # Shared tsconfig

  adapters/           # Typed clients into ZeSporteXte services
    vaultbrain-client/
    agent-gateway-client/
    api-client/       # OpenAPI-generated
    identity-client/

  config/             # Shared eslint, prettier configs

services/
  rat-os-api/         # BFF aggregator scaffold

contracts/            # OpenAPI + event schemas (RAT-OS ↔ ZeSporteXte)
infra/                # Vercel / Render / Docker
docs/                 # Product / architecture / governance / dev-reports / prototype-systems
.agents/              # AI orchestration framework (NJZPOF v0.2)
ROOT_AXIOMS/          # Founding principles, standards, procedures, references
```

---

## For AI Agents Starting a Session

1. Read `MASTER_PLAN.md` — current phase + scope.
2. Read `.agents/AGENT_CONTRACT.md` — what you can and cannot do.
3. Read `.agents/PHASE_GATES.md` — which phases are unlocked.
4. Read `.agents/SCHEMA_REGISTRY.md` — canonical types before defining new ones.
5. Check `.doc-tiers.json` before loading any `.md` file.

Do not load T2 files. They are archived for context efficiency.

---

## Relationship to ZeSporteXte

RAT-OS does not duplicate ZeSporteXte. It consumes:

- `@njz/ui` — shared design primitives
- `services/vaultbrain` (HTTP/WS) — persistent state + AI memory
- `services/agent-gateway` (HTTP) — agent + MCP routing
- `services/api` (REST, OpenAPI-generated client) — platform data

See `docs/architecture/INTEGRATION_WITH_ZESPORTEXTE.md` for the full contract surface.

---

## License

MIT — see `LICENSE`.

---

*Repository: `hvrryh-web/satorXrotas` · Upstream platform: `notbleaux/ZeSporteXte`*
