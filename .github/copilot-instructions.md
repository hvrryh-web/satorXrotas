# Copilot Instructions — SATOR / RadiantX

These instructions guide GitHub Copilot and AI coding agents working in the
SATOR monorepo. All agents must read this file before making changes.

---

## 1. Project Overview

**SATOR** is a three-part esports simulation and analytics platform:

| Component | Technology | Location |
|-----------|-----------|----------|
| **RadiantX** | Godot 4 / GDScript | `scripts/`, `scenes/`, `maps/`, `Defs/`, `tests/` |
| **Axiom Esports Data** | Python (analytics), React/TS/D3/WebGL (viz) | `axiom-esports-data/` |
| **SATOR Web** | TypeScript | `apps/sator-web/`, `api/`, `packages/` |

A **data partition firewall** (`packages/data-partition-lib/src/FantasyDataFilter.ts`)
prevents game-internal fields from ever reaching the web platform. The public type
contract lives in `packages/stats-schema/src/types/`. Full policy is at
`docs/FIREWALL_POLICY.md`.

---

## 2. Development Environment

### 2.1 Game (RadiantX)

- **Engine:** Godot 4.0+ — open `project.godot` in the Godot Editor.
- **Run:** Press F5 or play `scenes/Main.tscn`.
- **Tests:** Run `tests/test_determinism.tscn` from the Godot Editor.
- **No external dependencies** — Godot built-in classes only.

### 2.2 Web & Packages (TypeScript)

- **Runtime:** Node.js 20+
- **Install:** `npm install` at the repository root.
- **Build:** `npm run build`
- **Firewall tests:** `npm run test:firewall`
- **Schema validation:** `npm run validate:schema`
- **Type check:** `npm run typecheck`

### 2.3 Analytics (Python)

- **Runtime:** Python 3.11+
- **Install:** `cd axiom-esports-data/extraction && pip install -r requirements.txt`
- **Tests:** `cd axiom-esports-data/analytics && python -m pytest tests/`
- **Infrastructure:** `docker-compose -f axiom-esports-data/infrastructure/docker-compose.yml up -d`

### 2.4 CI Workflows

| Workflow | File | Purpose |
|----------|------|---------|
| Core structural validation | `.github/workflows/ci.yml` | Project structure, JSON, GDScript, docs, license |
| Schema validation | `.github/workflows/validate-sator-schema.yml` | Stats-schema firewall compliance |
| Firewall tests | `.github/workflows/test-firewall.yml` | Data partition enforcement |

---

## 3. Task Structured Format

Every GitHub task an AI agent works on must follow the structured format below.
This ensures traceability, consistency, and clear audit trails.

### 3.1 Introduction Assessment (start of task)

Before making any changes, the agent must document:

```
## Task Introduction
- **Issue/PR:** #<number> — <title>
- **Scope:** <brief description of what will change>
- **Files affected:** <list of files expected to be modified>
- **Risk assessment:** LOW | MEDIUM | HIGH
- **Firewall impact:** YES | NO — does this touch data flowing to/from the web?
- **Determinism impact:** YES | NO — does this touch simulation logic?
- **Analytics impact:** YES | NO — does this touch the analytics pipeline or guardrails?
```

### 3.2 Patch Log (during task)

Track every meaningful change as it is made:

```
## Patch Log
| # | File | Change Summary | Reason |
|---|------|---------------|--------|
| 1 | path/to/file.ts | Added field `clutchRate` to Statistics type | New public stat requirement |
| 2 | docs/FIREWALL_POLICY.md | Added row to PUBLIC fields table | Keep docs in sync |
```

### 3.3 Conclusion Assessment (end of task)

After all changes are complete, the agent must document:

```
## Task Conclusion
- **Changes made:** <summary of all modifications>
- **Tests run:** <list of tests executed and their results>
- **Firewall status:** PASS | FAIL | N/A
- **Determinism status:** PASS | FAIL | N/A
- **Documentation updated:** YES | NO — list any docs changed
- **Outstanding items:** <anything deferred or requiring follow-up>
```

---

## 4. AI Agent Behavior Protocols

### 4.1 General Conduct

1. **Read before writing.** Always review the file and its surrounding context
   before making changes.
2. **Minimal changes.** Modify only what is necessary. Do not refactor unrelated code.
3. **Preserve existing patterns.** Match the style, naming, and structure already
   present in the file.
4. **Validate changes.** Run relevant tests and linting after every modification.
5. **Never delete working code** unless the task explicitly requires removal.
6. **Never commit secrets, credentials, or API keys.**

### 4.2 Commenting and Documentation Guidelines

When an AI agent modifies code, follow these documentation standards:

- **Inline comments:** Add only when the code is non-obvious or implements a
  workaround. Match the commenting style already used in the file.
- **Function/method docs:** Add or update JSDoc (TypeScript), docstrings (Python),
  or `##` comments (GDScript) for any new or changed public function.
- **PR descriptions:** Always include the Introduction Assessment and Conclusion
  Assessment (see Section 3) in the PR body or progress report.
- **Changelog entries:** For user-facing changes, note them in the Patch Log.
- **File-level comments:** Do not add boilerplate headers to files unless the
  project already uses them.

### 4.3 Commit Message Format

```
<type>: <short description>

Types: feat | fix | chore | docs | refactor | test
```

Examples:
- `feat: add clutchRate to public stats schema`
- `fix: restore determinism in agent processing order`
- `docs: update FIREWALL_POLICY with new field classification`

---

## 5. Data Integration and Staging Guidelines

### 5.1 Data Flow Architecture

```
Game Simulation (GDScript)
    │
    ▼
FantasyDataFilter.sanitizeForWeb()    ← FIREWALL
    │
    ▼
API Layer (TypeScript)
    │
    ▼
SATOR Web / Public Stats
```

### 5.2 Data Classification Rules

| Classification | Rule | Action |
|---------------|------|--------|
| **GAME-ONLY** | Internal simulation state | Add to `GAME_ONLY_FIELDS` in `FantasyDataFilter.ts` |
| **PUBLIC** | Derivable from match results, meaningful to users | Add to `packages/stats-schema/src/types/` |

**Blocked fields** (never expose to web):
`internalAgentState`, `radarData`, `detailedReplayFrameData`, `simulationTick`,
`seedValue`, `visionConeData`, `smokeTickData`, `recoilPattern`

### 5.3 Data Integration Staging Workflow

When adding or modifying data that flows between components:

1. **Classify the data.** Determine if it is GAME-ONLY or PUBLIC using the decision
   tree in `docs/FIREWALL_POLICY.md`.
2. **Define the type.** If PUBLIC, add the TypeScript type to
   `packages/stats-schema/src/types/`.
3. **Update the filter.** If GAME-ONLY, add the field name to
   `FantasyDataFilter.GAME_ONLY_FIELDS`.
4. **Update documentation.** Update `docs/FIREWALL_POLICY.md` with the
   classification.
5. **Validate.** Run `npm run test:firewall` and `npm run validate:schema`.

### 5.4 Analytics Data Pipeline

When modifying the Axiom Esports Data pipeline:

1. **Guardrails are mandatory.** All analytics must pass through
   `guardrails/temporal_wall.py` to prevent future data leakage.
2. **Data integrity first.** All input data must pass through
   `storage/integrity_checker.py` (SHA-256 checksums).
3. **Dual-storage protocol.** Raw data is immutable (append-only);
   reconstructed data can be rebuilt from raw sources.
4. **Confidence scoring.** Use `guardrails/confidence_sampler.py` for any
   statistical calculations.

---

## 6. Coding Standards by Language

### 6.1 GDScript (Game — `scripts/`)

| Rule | Detail |
|------|--------|
| Indentation | **Tabs** (not spaces) |
| Variables/functions | `snake_case` |
| Classes | `PascalCase` with `class_name` declaration |
| Constants | `UPPER_SNAKE_CASE` |
| Private members | Leading underscore (`_process_combat()`) |
| Randomness | **Only** seeded `RandomNumberGenerator` — never `randf()`/`randi()` |
| Timestep | Fixed 20 TPS (50ms) — never use delta-time in simulation logic |
| Communication | Signals for decoupled inter-system messaging |
| Data pattern | `*Def` for static definitions, `*State` for runtime state |

### 6.2 TypeScript (Packages, Web — `packages/`, `apps/`, `api/`)

| Rule | Detail |
|------|--------|
| Mode | `strict: true` always |
| Types | Import from `@sator/stats-schema` — never re-define inline |
| Firewall | Always call `FantasyDataFilter.sanitizeForWeb()` before sending game data |
| No `any` | Avoid `any` unless absolutely necessary with explicit justification |

### 6.3 Python (Analytics — `axiom-esports-data/`)

| Rule | Detail |
|------|--------|
| Style | PEP 8 |
| Type hints | Required on all function signatures |
| Temporal wall | Never use future data in calculations |
| Testing | `pytest` with descriptive test names |

### 6.4 React/D3/WebGL (Visualization — `axiom-esports-data/visualization/`)

| Rule | Detail |
|------|--------|
| Components | Functional components with hooks |
| Accessibility | Protanopia-safe colors, ARIA labels, keyboard navigation |
| SVG | Use for <200 elements (D3.js) |
| WebGL | Use for >1000 elements (shaders in `visualization/shaders/`) |
| Performance | Target 60 FPS |

---

## 7. Application Development Protocols

### 7.1 Adding a New Feature

1. Identify which component the feature belongs to (Game, Analytics, Web).
2. Create a feature branch from `develop`: `feature/<name>`.
3. Complete the Introduction Assessment (Section 3.1).
4. Implement the feature following language-specific standards (Section 6).
5. Maintain the Patch Log (Section 3.2).
6. Run all relevant tests.
7. Complete the Conclusion Assessment (Section 3.3).
8. Open a PR to `develop`.

### 7.2 Adding a New Public Stat

1. Verify the field is derivable from match results (not simulation-internal).
2. Add the field to `packages/stats-schema/src/types/Statistics.ts`.
3. Add a row to the PUBLIC fields table in `docs/FIREWALL_POLICY.md`.
4. Run `npm run test:firewall` and `npm run validate:schema`.

### 7.3 Adding a New Game Feature

1. Edit files in `scripts/` following determinism rules.
2. If the feature produces new data, classify it (Section 5.2).
3. Run `tests/test_determinism.tscn` to verify determinism is preserved.

### 7.4 Adding a New Analytics Metric

1. Create a module under `axiom-esports-data/analytics/`.
2. Enforce temporal wall constraints.
3. Add unit tests.
4. Document the metric in `axiom-esports-data/docs/DATA_DICTIONARY.md`.

### 7.5 Modifying CI Workflows

1. Use `actions/checkout@v4` and `actions/setup-node@v4` with `node-version: '20'`.
2. Never break existing `ci.yml` checks.
3. Never weaken firewall checks in `test-firewall.yml`.
4. Reference `.github/workflows/ci.yml` for naming and structure conventions.

---

## 8. Management and Parsing Guidelines

### 8.1 JSON Data Management

- **Map files** (`maps/*.json`): Follow the schema in `docs/map_format.md`.
- **Definition files** (`Defs/`): Agents, weapons, utilities, and rulesets loaded
  by `DataLoader.gd` at runtime.
- **Replay files** (`user://replay_*.json`): Tick-timestamped event logs for
  full match reconstruction.

### 8.2 Data Parsing Rules

- All JSON files must parse cleanly — CI validates this.
- Use the existing `DataLoader.gd` singleton for game definition loading.
- For analytics data, use `extraction/parsers/` modules (match_parser,
  role_classifier, economy_inference).
- Never parse game-internal JSON in web components.

### 8.3 Branch Management

| Branch | Purpose | Merge Target |
|--------|---------|-------------|
| `main` | Production — all tests pass | — |
| `develop` | Integration — features merged here | `main` |
| `feature/*` | Feature development | `develop` |

See `docs/BRANCH_STRATEGY.md` for the full branching model.

---

## 9. Key Reference Files

| File | Purpose |
|------|---------|
| `docs/FIREWALL_POLICY.md` | Data partition firewall rules |
| `docs/architecture.md` | System design and data flow |
| `docs/PROJECT_STRUCTURE.md` | Repository directory layout |
| `docs/agents.md` | Agent AI behavior documentation |
| `docs/map_format.md` | JSON map specification |
| `docs/replay.md` | Replay system documentation |
| `docs/BRANCH_STRATEGY.md` | Git branching model |
| `CONTRIBUTING.md` | Contribution guidelines |
| `CLAUDE.md` | Claude AI assistant guide |
| `.github/SATOR-COPILOT-PROMPTS.md` | Detailed AI prompting templates |
| `axiom-esports-data/AXIOM.md` | Analytics pipeline operational guide |
| `axiom-esports-data/docs/DATA_DICTIONARY.md` | 37-field KCRITR schema |

---

## 10. Critical Invariants

These rules must **never** be violated:

1. **Firewall integrity.** `GAME_ONLY_FIELDS` must never appear in
   `packages/stats-schema` types or in web-facing responses.
2. **Simulation determinism.** Same seed must always produce identical event
   logs. Only seeded RNG, fixed 20 TPS timestep, consistent agent ordering.
3. **Temporal wall.** Analytics must never use future data in calculations.
4. **Dual-storage immutability.** Raw data tables are append-only.
5. **Existing files preserved.** Do not delete or move existing Godot files,
   scene files, or map files unless the task explicitly requires it.
6. **Strict TypeScript.** All TypeScript must compile with `strict: true`.
