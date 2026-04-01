# SATOR Project Structure

## Overview

SATOR is a two-part esports simulation platform:
- **RadiantX** — Offline deterministic tactical FPS game (Godot 4 / GDScript)
- **SATOR Web** — Online public statistics platform (TypeScript / web)

This document describes the complete repository structure, explains the purpose of each
directory, and describes how the firewall fits into the overall layout.

---

## Full Directory Tree

```
RadiantX/  (repository root — also called "sator" monorepo)
│
├── apps/                           # Deployable applications
│   ├── radiantx-game/              # Offline game application
│   │   ├── src/                    # New game modules (Phase 2+)
│   │   │   └── README.md           # LiveSeasonModule placeholder
│   │   └── build/                  # Build artifacts (gitignored)
│   └── sator-web/                  # Online web platform (Phase 3+)
│       └── src/                    # Web application source
│
├── api/                            # SATOR backend API (Phase 3+)
│   └── src/                        # API source code
│       └── README.md               # Firewall middleware placeholder
│
├── packages/                       # Shared TypeScript packages
│   ├── stats-schema/               # Public stats type definitions
│   │   ├── src/
│   │   │   └── types/
│   │   │       ├── index.ts        # Re-exports all public types
│   │   │       ├── Player.ts       # Player identity and profile
│   │   │       ├── Match.ts        # Match metadata
│   │   │       ├── Season.ts       # Season and ranking
│   │   │       └── Statistics.ts   # Performance stats
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── README.md
│   ├── data-partition-lib/         # Firewall enforcement library
│   │   ├── src/
│   │   │   └── FantasyDataFilter.ts # Core firewall filter class
│   │   ├── package.json
│   │   └── README.md
│   └── api-client/                 # TypeScript API client (Phase 4+)
│       └── src/
│           └── README.md
│
├── scripts/                        # Core Godot game logic (GDScript)
│   ├── README.md                   # Scripts directory guide
│   ├── Main.gd                     # Entry point
│   ├── MatchEngine.gd              # 20 TPS simulation
│   ├── Agent.gd                    # Agent AI
│   ├── Data/                       # Data types (22 files)
│   └── Sim/                        # Combat subsystem (6 files)
│
├── scenes/                         # Godot scene files
├── maps/                           # Game map JSON files
├── Defs/                           # Game definition JSON files
├── tests/                          # Godot determinism tests (GDScript)
│   ├── test_determinism.gd
│   └── test_determinism.tscn
│
├── docs/                           # All project documentation
│   ├── FIREWALL_POLICY.md          # ★ Critical: data partition rules
│   ├── PROJECT_STRUCTURE.md        # This file
│   ├── BRANCH_STRATEGY.md          # Git branch strategy
│   ├── architecture.md             # System architecture overview
│   ├── agents.md                   # Agent AI documentation
│   ├── map_format.md               # Map JSON specification
│   ├── replay.md                   # Replay system guide
│   ├── quick_start.md              # Getting started guide
│   ├── custom-agents.md            # AI agent configuration
│   ├── game/                       # Game-specific docs (Phase 2)
│   │   └── README.md
│   ├── web/                        # Web platform docs (Phase 3)
│   │   └── README.md
│   └── api/                        # API docs (Phase 3)
│       └── README.md
│
├── .github/
│   ├── SATOR-COPILOT-PROMPTS.md    # AI-assisted development guide
│   ├── CODEOWNERS                  # Code review ownership
│   └── workflows/
│       ├── ci.yml                  # Core CI validation
│       ├── validate-sator-schema.yml # Schema validation workflow
│       └── test-firewall.yml       # Firewall enforcement tests
│
├── package.json                    # Root npm workspace config
├── .env.example                    # Environment variable template
├── project.godot                   # Godot project entry point
├── README.md                       # Repository overview
├── CONTRIBUTING.md                 # Contribution guide
├── PROJECT_SUMMARY.md              # Project summary
└── LICENSE                         # MIT license
```

---

## Purpose of Each Major Directory

### `apps/`

Deployable applications. Each app consumes packages from `packages/` and is
independently deployable.

| App | Description |
|-----|-------------|
| `apps/radiantx-game/` | The offline Godot game. New TypeScript integration modules live here. The existing Godot source remains in `scripts/` at the root. |
| `apps/sator-web/` | The public web platform. Displays stats using `@sator/stats-schema` types. Never imports game code directly. |

### `packages/`

Shared TypeScript libraries used by apps and API. Each package has its own
`package.json` and `tsconfig.json`.

| Package | Description |
|---------|-------------|
| `packages/stats-schema` | Defines all public data types. This is the contract between the game, API, and web. |
| `packages/data-partition-lib` | Contains `FantasyDataFilter` — the firewall enforcement class. |
| `packages/api-client` | TypeScript HTTP client for the SATOR API (Phase 4). |

### `api/`

The SATOR backend API. Receives match data from the game, applies the firewall
filter, stores clean stats in the database, and serves them to the web.

### `docs/`

All project documentation. Game documentation currently lives at the `docs/` root
level. In Phase 2 it will be organized into `docs/game/`, `docs/web/`, and `docs/api/`
subdirectories.

### `scripts/`

Build and automation shell scripts. Not to be confused with the Godot `scripts/`
directory which contains GDScript game logic.

### `tests/`

Integration and E2E tests for the TypeScript components. Godot-specific tests remain
in the root `tests/` directory (`test_determinism.tscn`).

---

## How the Firewall Fits In

```
packages/data-partition-lib   ← defines the rules
          │
          │  used by
          ▼
apps/radiantx-game/src/LiveSeasonModule.gd   ← extracts public data
          │
          │  sends to
          ▼
api/src/middleware/firewallMiddleware.ts      ← enforces at API boundary
          │
          │  stores
          ▼
Database (only stats-schema types)
          │
          │  reads
          ▼
apps/sator-web/                              ← displays public data
```

The key invariant: **game code never imports web code; web code never imports game code.**
All communication goes through the API with firewall middleware in between.

---

## File Organization Rationale

### Why keep existing Godot files at root level?

The existing `scripts/`, `scenes/`, `maps/`, `Defs/`, and `tests/` (GDScript) live at
the root to preserve the `project.godot` relative path references. Moving them would
break the Godot project. New integration code for the game goes in
`apps/radiantx-game/src/`.

### Why a monorepo?

SATOR's game and web components share type definitions (`stats-schema`). A monorepo
allows these shared types to be developed, versioned, and tested together without
publishing to npm.

### Why separate `data-partition-lib`?

Isolating the firewall into its own package ensures:
- It can be tested independently of the API and game
- Its `GAME_ONLY_FIELDS` list is the single source of truth
- Changes require an explicit PR review (enforced by CODEOWNERS)

---

## Phase-by-Phase Implementation

| Phase | Focus | Key Files |
|-------|-------|-----------|
| **Phase 1** | Foundation, docs, structure | Everything in this PR |
| **Phase 2** | Stats schema types | `packages/stats-schema/src/types/*.ts` |
| **Phase 3** | Firewall implementation + API | `packages/data-partition-lib/`, `api/` |
| **Phase 4** | Web platform | `apps/sator-web/`, `packages/api-client/` |
| **Phase 5** | E2E integration + tests | `tests/`, CI workflows |

---

*See also: [FIREWALL_POLICY.md](FIREWALL_POLICY.md) · [BRANCH_STRATEGY.md](BRANCH_STRATEGY.md) · [architecture.md](architecture.md)*
