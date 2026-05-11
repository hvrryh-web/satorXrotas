# Repository Domain Blueprint

## Core Domains
- `apps/` - End-user app surfaces
- `extensions/` - Browser extension code
- `services/` - Backend services and APIs
- `packages/` - Shared logic and UI
- `docs/` - Product, architecture, ADRs, onboarding
- `infra/` - Infrastructure and deployment assets

## Target Structure
```
scaffold/
├── apps/
│   ├── webapp/
│   └── website/
├── extensions/
│   └── browser-extension/
├── services/
│   └── api/
├── packages/
│   ├── ai-adapter/
│   ├── planner-core/
│   └── ui-sprite-kit/
├── docs/
└── infra/
```

## Domain Responsibilities
- **webapp**: planner UI, simulation dashboard, authenticated user workspace
- **website**: public marketing and docs experience
- **browser-extension**: context capture and quick task submission
- **api service**: auth, project data, planner orchestration, simulation state
- **ai-adapter**: provider abstraction, prompts, model safety checks
- **planner-core**: workflow states, task lifecycle, sprint logic
- **ui-sprite-kit**: pixel sprite rendering, state machine, animation hooks
