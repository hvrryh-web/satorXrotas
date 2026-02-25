# SATOR Copilot Prompting Guide

Comprehensive guide for AI-assisted development of the SATOR esports simulation
platform. Use the prompts in this file to give GitHub Copilot, Claude, or any AI
assistant the context needed to produce correct, firewall-compliant code.

---

## Quick Reference

| Part | When to Use |
|------|------------|
| [Part A](#part-a-context-setting-prompts) | Start of a new session — set the stage |
| [Part B](#part-b-task-specific-templates) | Implementing a specific feature |
| [Part C](#part-c-validation-prompts) | Reviewing or verifying AI output |
| [Part D](#part-d-emergency-prompts) | Debugging unexpected behavior |
| [Part E](#part-e-full-context-master-prompt) | Complex multi-file changes |
| [Part F](#part-f-branch-specific-context) | Working on a specific branch |

---

## Part A: Context-Setting Prompts

Use these at the start of a new AI session to ensure the assistant understands the
project architecture and constraints.

### A1 — General Project Context

```yaml
prompt: |
  You are working on the SATOR monorepo — an esports simulation platform with two
  components:

  1. RadiantX — An offline deterministic tactical FPS simulation game built with
     Godot 4 and GDScript. Lives in scripts/, scenes/, maps/, Defs/, and
     apps/radiantx-game/src/.

  2. SATOR Web — An online public statistics platform (TypeScript, not yet
     implemented). Lives in apps/sator-web/.

  Key constraint: A DATA PARTITION FIREWALL separates these two components.
  Game-internal data (radarData, simulationTick, seedValue, internalAgentState,
  visionConeData, smokeTickData, recoilPattern, detailedReplayFrameData) must
  NEVER reach the web platform.

  Enforcement is in packages/data-partition-lib/src/FantasyDataFilter.ts.
  The public type contract is in packages/stats-schema/src/types/.

  Full policy: docs/FIREWALL_POLICY.md
  Structure: docs/PROJECT_STRUCTURE.md

  Do not move or delete existing Godot files. Do not add game-internal fields to
  packages/stats-schema. Always use TypeScript strict mode.
```

### A2 — Game Development Context

```yaml
prompt: |
  You are working on the RadiantX offline game component of the SATOR monorepo.

  Technology: Godot 4.x, GDScript
  Location: scripts/, scenes/, maps/, Defs/, apps/radiantx-game/src/

  Architecture:
  - MatchEngine.gd — 20 TPS deterministic simulation loop
  - Agent.gd — AI agents with partial observability
  - MapData.gd — Map loading and LOS calculations
  - EventLog.gd — Match event recording
  - Viewer2D.gd — Top-down 2D rendering
  - PlaybackController.gd — Replay controls

  Coding rules:
  1. All simulation logic must be deterministic — only seeded RNG, fixed timestep
  2. GDScript naming: snake_case for variables/functions, PascalCase for classes
  3. Use tabs (not spaces) for indentation
  4. Emit signals for decoupled communication
  5. Separate *Def (static) and *State (runtime) data classes

  Do NOT add web/TypeScript code to game files. The game communicates with the
  API only through apps/radiantx-game/src/LiveSeasonModule.gd (Phase 2).
```

### A3 — Web Platform Context

```yaml
prompt: |
  You are working on the SATOR Web platform component.

  Technology: TypeScript (framework TBD in Phase 3)
  Location: apps/sator-web/src/

  CRITICAL FIREWALL RULE:
  - This component may ONLY display fields defined in packages/stats-schema
  - It must NEVER import from game source (scripts/, apps/radiantx-game/)
  - All data arrives pre-sanitized through the API layer

  Allowed data types (from @sator/stats-schema):
  - Player — id, username, region, rankTier, rankPoints
  - Match — id, mapName, startedAt, endedAt, winnerSide, roundsPlayed
  - Statistics — kills, deaths, assists, damage, headshots, utilityDamage,
                 roundsWon, firstKills, clutchesWon

  Forbidden fields — never display these, never fetch these:
  internalAgentState, radarData, detailedReplayFrameData, simulationTick,
  seedValue, visionConeData, smokeTickData, recoilPattern

  Always import types from @sator/stats-schema. Always use strict TypeScript.
```

### A4 — API and CI/CD Context

```yaml
prompt: |
  You are working on the SATOR API and/or CI/CD workflows.

  API location: api/src/
  CI/CD location: .github/workflows/

  API responsibilities:
  - Receive match data from RadiantX game
  - Apply FantasyDataFilter.sanitizeForWeb() BEFORE any storage
  - Validate response bodies against @sator/stats-schema types
  - Serve public stats to SATOR Web platform

  Firewall middleware pattern:
    import { FantasyDataFilter } from '@sator/data-partition-lib';
    const safe = FantasyDataFilter.sanitizeForWeb(rawGameData);

  CI/CD rules:
  - validate-sator-schema.yml: Runs on PRs to main/develop
  - test-firewall.yml: Blocks merge if firewall tests fail
  - ci.yml: Core structural validation (existing — do not break)
  - All workflows use actions/checkout@v4 and actions/setup-node@v4

  Root package.json scripts:
  - test:firewall — Run firewall unit tests
  - validate:schema — Validate schema package
  - build — Build all packages
  - dev — Start development environment
```

---

## Part B: Task-Specific Prompting Templates

### B1 — Implementing a New Public Stat

Use when adding a new statistic that should appear on the web platform.

```yaml
prompt: |
  I need to add a new public statistic to the SATOR platform: [STAT_NAME].

  Follow this checklist exactly:

  STEP 1 — Verify it belongs in the public schema:
  - Is it derivable from match results without exposing simulation internals?
  - Is it meaningful to end users?
  - Is it NOT in the GAME_ONLY_FIELDS list in FantasyDataFilter.ts?
  If any answer is NO, do not proceed — explain why.

  STEP 2 — Add to packages/stats-schema/src/types/Statistics.ts:
  - Add the field with TypeScript type annotation
  - Add a JSDoc comment explaining what it measures
  - Do NOT add fields like simulationTick, seedValue, radarData, etc.

  STEP 3 — Add to docs/FIREWALL_POLICY.md:
  - Add a row to the PUBLIC Fields table

  STEP 4 — Update packages/stats-schema/src/types/index.ts if needed

  STEP 5 — Confirm that validate-sator-schema.yml will still pass:
  - The field name must NOT appear in GAME_ONLY_FIELDS

  Files to modify: packages/stats-schema/src/types/Statistics.ts,
                   docs/FIREWALL_POLICY.md
  Files NOT to modify: packages/data-partition-lib/src/FantasyDataFilter.ts
                       (unless the stat is game-only)
```

### B2 — Implementing a New Game Feature

Use when adding new logic to the RadiantX game simulation.

```yaml
prompt: |
  I need to add a new game feature: [FEATURE_NAME].

  Follow these rules for all game code:

  DETERMINISM (critical):
  - Only use the seeded RandomNumberGenerator instance (never Math.random() or
    OS.get_ticks_msec() for gameplay logic)
  - Process agents in a consistent order every tick
  - No floating point accumulation in critical paths

  GDSCRIPT STYLE:
  - snake_case for variables and functions
  - PascalCase for class names
  - Tabs for indentation (not spaces)
  - One class per file with class_name declaration

  FIREWALL:
  - If this feature produces new data, ask: "Is this game-internal or public?"
  - Game-internal data → add to FantasyDataFilter.GAME_ONLY_FIELDS
  - Public data → add to packages/stats-schema/src/types/Statistics.ts

  SIGNALS:
  - Use signals for decoupled communication between systems
  - MatchEngine emits: tick_processed, match_started, match_ended, round_ended

  Files to look at first:
  - scripts/MatchEngine.gd — Simulation loop
  - scripts/Agent.gd — Agent AI
  - scripts/Data/DataTypes.gd — Enums and constants
```

### B3 — Implementing Firewall/Security Changes

Use when modifying the data partition library or firewall policy.

```yaml
prompt: |
  I need to modify the SATOR data partition firewall.

  CAUTION: Changes to the firewall require careful review. Follow this process:

  1. READ docs/FIREWALL_POLICY.md completely before making any changes.

  2. If ADDING a new GAME_ONLY_FIELD:
     - Add to GAME_ONLY_FIELDS Set in FantasyDataFilter.ts
     - Add to the blocked fields table in docs/FIREWALL_POLICY.md
     - Add a test case in tests/firewall/ verifying it is stripped

  3. If REMOVING a GAME_ONLY_FIELD (removing a restriction):
     - Explain exactly why the field is safe to expose publicly
     - Add to packages/stats-schema types first
     - Update the PUBLIC fields table in docs/FIREWALL_POLICY.md
     - This should be extremely rare and requires justification

  4. NEVER:
     - Remove sanitizeForWeb() or validateWebInput() from FantasyDataFilter
     - Bypass the filter in API middleware
     - Add GAME_ONLY_FIELDS to packages/stats-schema types

  5. After changes, verify:
     - validate-sator-schema.yml will still catch violations
     - test-firewall.yml will still verify all fields are blocked
     - docs/FIREWALL_POLICY.md audit checklist is satisfied

  Files: packages/data-partition-lib/src/FantasyDataFilter.ts,
         docs/FIREWALL_POLICY.md, .github/workflows/test-firewall.yml
```

### B4 — Adding a CI/CD Workflow

Use when creating or modifying GitHub Actions workflows.

```yaml
prompt: |
  I need to create or modify a GitHub Actions workflow for SATOR.

  Conventions for SATOR workflows:
  - Use actions/checkout@v4 (not v3)
  - Use actions/setup-node@v4 with node-version: '20'
  - Add permissions: contents: read unless writes are needed
  - Name the job descriptively
  - End with a Summary step that echoes results

  Firewall-related workflows:
  - validate-sator-schema.yml: Triggers on changes to packages/stats-schema/**
    or packages/data-partition-lib/**
  - test-firewall.yml: Triggers on changes to packages/data-partition-lib/**
    or api/**

  Both firewall workflows must:
  - Check that GAME_ONLY_FIELDS are not in stats-schema types
  - Verify FantasyDataFilter has all required blocked fields
  - Block merge if any check fails

  Existing workflows (do not break):
  - ci.yml — Validates project structure, JSON, GDScript, docs, license

  Reference .github/workflows/ci.yml for the existing style.
  Reference .github/workflows/validate-sator-schema.yml for firewall style.
```

---

## Part C: Validation Prompts

Use these to verify AI-generated code or documentation before committing.

### C1 — Validate Documentation

```yaml
prompt: |
  Review this documentation for correctness and completeness:

  Checklist:
  1. Is the firewall concept explained clearly?
  2. Would a new developer understand what fields are blocked vs allowed?
  3. Are all code examples syntactically correct?
  4. Are all file paths accurate (check against docs/PROJECT_STRUCTURE.md)?
  5. Does it reference packages/data-partition-lib and packages/stats-schema
     correctly?
  6. Does it avoid disclosing GAME_ONLY_FIELDS in any examples?
  7. Would this guide effective AI-assisted development?

  Flag any issues and suggest specific corrections.
```

### C2 — Validate TypeScript Code

```yaml
prompt: |
  Review this TypeScript code for SATOR correctness:

  Checklist:
  1. Does it use strict TypeScript (no `any` unless absolutely necessary)?
  2. Does it import types from @sator/stats-schema (not from game source)?
  3. Does it call FantasyDataFilter.sanitizeForWeb() before sending game data?
  4. Does it call FantasyDataFilter.validateWebInput() on incoming data?
  5. Are there any GAME_ONLY_FIELDS referenced?
     (internalAgentState, radarData, simulationTick, seedValue, visionConeData,
      smokeTickData, recoilPattern, detailedReplayFrameData)
  6. Does error handling propagate firewall violations correctly?
  7. Are all types from @sator/stats-schema used (not re-defined inline)?

  If any check fails, explain what needs to change and why.
```

### C3 — Validate GDScript Code

```yaml
prompt: |
  Review this GDScript code for SATOR correctness:

  Checklist:
  1. Is all randomness going through the seeded RandomNumberGenerator?
     (Never randf(), randi() on the global RNG)
  2. Does it use tabs for indentation?
  3. Are variable/function names snake_case and class names PascalCase?
  4. Does it avoid floating point accumulation in simulation logic?
  5. Are agents processed in a consistent, deterministic order?
  6. Does it use signals for inter-system communication?
  7. If extracting data for the API: does it avoid including GAME_ONLY_FIELDS?
     (internalAgentState, radarData, simulationTick, seedValue, etc.)
  8. Is there a corresponding determinism test impact?

  If any check fails, explain what needs to change and why.
```

### C4 — Validate Firewall Compliance

```yaml
prompt: |
  Perform a full firewall compliance check on these changes:

  1. Check packages/stats-schema/src/types/ for any of these forbidden fields:
     internalAgentState, radarData, detailedReplayFrameData, simulationTick,
     seedValue, visionConeData, smokeTickData, recoilPattern

  2. Check any new API routes for missing FantasyDataFilter.sanitizeForWeb() call

  3. Check any new web components for direct game data imports

  4. Verify packages/data-partition-lib/src/FantasyDataFilter.ts still contains:
     - GAME_ONLY_FIELDS Set with all 8 required fields
     - sanitizeForWeb() method
     - validateWebInput() method

  5. Confirm docs/FIREWALL_POLICY.md is consistent with code changes

  Report: PASS or FAIL with specific file:line references for any failures.
```

---

## Part D: Emergency Prompts

Use these when something has gone wrong or behavior is unexpected.

### D1 — Debug Firewall Violation

```yaml
prompt: |
  A game-internal field has appeared in web output. Help me trace the leak.

  Known GAME_ONLY_FIELDS: internalAgentState, radarData, detailedReplayFrameData,
  simulationTick, seedValue, visionConeData, smokeTickData, recoilPattern

  Violation: [DESCRIBE WHAT FIELD APPEARED WHERE]

  Trace the data flow:
  1. Where is this field set in the game? (search scripts/)
  2. Is it extracted in apps/radiantx-game/src/LiveSeasonModule.gd?
  3. Does FantasyDataFilter.GAME_ONLY_FIELDS include this field?
  4. Does the API middleware call sanitizeForWeb() before storing?
  5. Does the web component have any direct game imports?

  Output a root cause analysis and a specific fix for each gap in the chain.
```

### D2 — Fix Failing CI

```yaml
prompt: |
  A GitHub Actions workflow is failing. Help me fix it.

  Repository: hvrryh-web/RadiantX
  Failing workflow: [WORKFLOW NAME]
  Error output: [PASTE ERROR HERE]

  Constraints:
  - Do not break the existing ci.yml (it validates project structure)
  - Do not weaken firewall checks in test-firewall.yml
  - Do not remove required fields from validate-sator-schema.yml
  - Fix only the failing step; do not refactor unrelated steps

  Output: The specific file change needed and why it fixes the failure.
```

### D3 — Restore Determinism

```yaml
prompt: |
  The RadiantX game simulation has lost determinism — the same seed produces
  different results on repeated runs.

  Possible causes (check in this order):
  1. Non-seeded randomness — search for randf(), randi(), RandomNumberGenerator
     calls that don't use the seeded instance
  2. Dictionary ordering — GDScript dicts don't guarantee order; sort keys before
     iterating
  3. Delta-time dependency — search for delta-based calculations in simulation
     code (should use fixed 50ms tick)
  4. Agent processing order — agents must always be processed in the same order
  5. Signal ordering — check that signal handlers fire in a consistent order

  Run tests/test_determinism.tscn in Godot to reproduce.
  Compare event logs from two runs with the same seed.
  Report which tick and event diverge first.
```

### D4 — Recover from Accidental GAME_ONLY_FIELD in Schema

```yaml
prompt: |
  A GAME_ONLY_FIELD has been accidentally added to packages/stats-schema.
  The validate-sator-schema.yml CI is failing.

  Immediate steps:
  1. Identify the offending field in packages/stats-schema/src/types/
  2. Remove the field from the schema type file
  3. Check if any web code depends on this field — if so, remove those uses too
  4. Confirm the field IS listed in FantasyDataFilter.GAME_ONLY_FIELDS
     (add it if missing)
  5. Update docs/FIREWALL_POLICY.md to classify the field as GAME-ONLY
  6. Run validate-sator-schema.yml locally to confirm the fix

  Do not add the field back to schema unless it has been reclassified as public
  following the decision tree in docs/FIREWALL_POLICY.md.
```

---

## Part E: Full Context Master Prompt

Use this for complex multi-file changes that span the game, API, and web layers.

```yaml
prompt: |
  You are working on SATOR — a two-part esports simulation platform.

  ## Architecture

  ### Component 1: RadiantX (Offline Game)
  - Engine: Godot 4.x, GDScript
  - Location: scripts/, scenes/, maps/, Defs/, apps/radiantx-game/
  - Core: MatchEngine.gd (20 TPS sim), Agent.gd (AI), EventLog.gd (replay)
  - Determinism: seeded RNG, fixed 50ms tick, consistent ordering
  - Style: snake_case, tabs, signals, *Def/*State pattern

  ### Component 2: SATOR Web (Online Platform)
  - Technology: TypeScript (Phase 3)
  - Location: apps/sator-web/, api/
  - Types: packages/stats-schema (ONLY these types may appear in web)
  - Firewall: packages/data-partition-lib (ALWAYS call sanitizeForWeb)

  ## Critical Invariants

  1. GAME_ONLY_FIELDS never reach web:
     internalAgentState, radarData, detailedReplayFrameData, simulationTick,
     seedValue, visionConeData, smokeTickData, recoilPattern

  2. All game data passes through FantasyDataFilter.sanitizeForWeb() before API

  3. Web layer imports types ONLY from @sator/stats-schema

  4. Game simulation MUST remain deterministic

  5. Existing files are not moved or deleted in Phase 1

  ## Key Files

  | File | Purpose |
  |------|---------|
  | docs/FIREWALL_POLICY.md | Firewall rules — read this first |
  | docs/PROJECT_STRUCTURE.md | Directory layout |
  | packages/data-partition-lib/src/FantasyDataFilter.ts | Core firewall |
  | packages/stats-schema/src/types/index.ts | Public type exports |
  | scripts/MatchEngine.gd | Game simulation loop |
  | scripts/Agent.gd | Agent AI |
  | .github/workflows/test-firewall.yml | Firewall CI |
  | .github/workflows/validate-sator-schema.yml | Schema CI |

  ## Current Phase

  Phase 1 — Foundation complete. Implementing: [DESCRIBE YOUR TASK HERE]

  ## Task

  [DESCRIBE YOUR SPECIFIC TASK]

  ## Constraints

  - Do not break existing ci.yml checks
  - Do not add GAME_ONLY_FIELDS to stats-schema
  - Do not delete or move existing Godot files
  - All TypeScript must use strict mode
  - All GDScript must be deterministic
```

---

## Part F: Branch-Specific Context

### F1 — Working on `main`

```yaml
prompt: |
  You are making a change directly to the `main` branch of SATOR.
  This is a PRODUCTION branch — apply maximum caution.

  Requirements for changes to main:
  - All CI workflows must pass after your change
  - Firewall must be intact (test-firewall.yml passes)
  - Schema must be valid (validate-sator-schema.yml passes)
  - No GAME_ONLY_FIELDS in public types
  - No deletions of existing Godot files

  If your change touches packages/data-partition-lib/ or docs/FIREWALL_POLICY.md,
  add explicit justification in the PR description.

  Run the audit checklist in docs/FIREWALL_POLICY.md before finalizing.
```

### F2 — Working on `develop`

```yaml
prompt: |
  You are working on the `develop` integration branch of SATOR.

  This branch integrates completed features before they go to main.

  Requirements:
  - ci.yml must pass
  - validate-sator-schema.yml must pass
  - No GAME_ONLY_FIELDS in stats-schema types
  - TypeScript must compile without errors

  Note: test-firewall.yml also runs on PRs to develop — verify it passes.

  If implementing Phase 2 or later work, follow the phase guidance in
  docs/PROJECT_STRUCTURE.md.
```

### F3 — Working on a `feature/*` branch

```yaml
prompt: |
  You are working on a feature branch: feature/[BRANCH_NAME].

  Branch-from: develop
  Merge-into: develop (via PR)

  Checklist before opening PR:
  - [ ] No GAME_ONLY_FIELDS added to packages/stats-schema
  - [ ] FantasyDataFilter.GAME_ONLY_FIELDS unchanged (or intentionally updated)
  - [ ] ci.yml checks pass
  - [ ] TypeScript compiles without errors (if any TS files changed)
  - [ ] GDScript determinism preserved (if any .gd files changed)
  - [ ] docs/ updated if behavior changed

  PR title format: [type]: short description
  Types: feat | fix | chore | docs | refactor | test
```

---

## Usage Examples

### Starting a new AI session to add a stat

1. Paste **Part A — A1** to set project context
2. Paste **Part B — B1** with `[STAT_NAME]` filled in
3. After AI proposes changes, run **Part C — C4** (firewall check)

### Debugging a CI failure

1. Get the error from GitHub Actions (SATOR → Actions tab → failing run)
2. Paste **Part D — D2** with the error output
3. Apply the fix and verify with **Part C — C2** or **C3**

### Implementing a full new feature (multi-file)

1. Paste **Part E** (master prompt) with your task filled in
2. After implementation, run **Part C — C4** (firewall) and **C1** (docs)
3. If touching GDScript, also run **Part C — C3**

### Emergency: game-internal data appeared in web

1. Immediately paste **Part D — D1** with the field name and location
2. Follow the trace to find all gaps
3. After fixing, run **Part C — C4** for full compliance check

---

## Summary

| Use Case | Prompt |
|----------|--------|
| Start session (general) | A1 |
| Start session (game work) | A2 |
| Start session (web work) | A3 |
| Start session (API / CI) | A4 |
| Add new public stat | B1 |
| Add new game feature | B2 |
| Modify firewall | B3 |
| Add CI workflow | B4 |
| Review any docs | C1 |
| Review TypeScript | C2 |
| Review GDScript | C3 |
| Full firewall audit | C4 |
| Trace field leak | D1 |
| Fix failing CI | D2 |
| Restore determinism | D3 |
| Remove field from schema | D4 |
| Complex multi-file task | E (master) |
| Working on main | F1 |
| Working on develop | F2 |
| Working on feature branch | F3 |

---

*This file is the primary prompting resource for SATOR AI-assisted development.
Keep it up to date as the project evolves through its phases.*

*Repository: https://github.com/hvrryh-web/RadiantX*
*Policy reference: docs/FIREWALL_POLICY.md*
*Structure reference: docs/PROJECT_STRUCTURE.md*
