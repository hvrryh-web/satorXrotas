[Ver001.000]

# SKILL_MAP — NJZ RAT-OS

Which agent owns which competence. Use this to route work and to know who to defer to. Owners are *agent roles*, not specific humans.

## Roles

| Role | Color | Responsibility |
|------|-------|----------------|
| **Architect** | TEAL | System design, ADRs, schema decisions |
| **Implementer** | ORANGE | Feature code, scaffolding, refactors |
| **Designer** | PURPLE | Design tokens, primitives, visual language |
| **Data Engineer** | BLUE | Adapters, contracts, OpenAPI, event pipelines |
| **Platform** | YELLOW | CI, infra, deployment, observability |
| **Critic** | RED | Code review, test coverage, security |
| **Coordinator** | GREEN | Framework, docs hygiene, multi-agent comms |

## Skill Ownership

| Skill | Primary | Secondary |
|-------|---------|-----------|
| TypeScript domain modeling | Architect | Implementer |
| React 19 / Vite | Implementer | Designer |
| Next.js 15 App Router | Implementer | Designer |
| Tailwind + tokens | Designer | Implementer |
| Web Audio API + binaural synthesis | Implementer | Architect |
| HTML5 Canvas / WebGL / Three.js | Implementer | Architect |
| Isometric pixel-art rendering | Implementer | Designer |
| XState state machines | Architect | Implementer |
| Zustand / TanStack Query | Implementer | Architect |
| OpenAPI / contract authoring | Data Engineer | Architect |
| FastAPI / Python services | Data Engineer | Platform |
| Postgres / Redis / async patterns | Data Engineer | Platform |
| Docker / Vercel / Render deploys | Platform | Data Engineer |
| GitHub Actions / pre-commit | Platform | Coordinator |
| Playwright / Vitest / coverage | Critic | Implementer |
| Accessibility (WCAG AA) | Designer | Critic |
| Security / secrets / SAST | Critic | Platform |
| ADR / documentation | Architect | Coordinator |
| Cross-repo coordination (ZeSporteXte) | Coordinator | Architect |
| AI agent contracts / .agents/ | Coordinator | Architect |

## Cross-Repo Skills (Read-Only Access to ZeSporteXte)

| Skill | Owner | Notes |
|-------|-------|-------|
| Mirror upstream `.agents/` conventions | Coordinator | Don't drift; pull updates into NJZPOF |
| Track upstream `@njz/*` releases | Data Engineer | Bump adapter versions accordingly |
| Coordinate with upstream service owners | Architect | Don't change their interfaces unilaterally |

## How To Request Routing

If you're starting work that's not in your primary skill:

1. Check this table; identify the primary owner role.
2. If you ARE that role for this session, proceed.
3. If you ARE NOT, ask the user whether to defer.
4. Override is fine if the user OKs it. Log the decision in `.agents/DECISION_LOG.md`.

## Adding a Skill

When a new technical area enters scope (e.g. mobile-native build, WASM module, OAuth flow), add a row here in the same PR as the first work item touching it.
