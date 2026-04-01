# Satire-deck-Veritas Repository Restructuring Plan
## Formerly: satorXrotas → Migration & Reorganization

---

## EXECUTIVE SUMMARY

**Repository:** `satorXrotas` → **Rename to:** `Satire-deck-Veritas`
**Current State:** Active development with scattered architecture
**Target State:** Clean separation of legacy, context, and active frameworks

---

## REPOSITORY STRUCTURE (NEW)

```
Satire-deck-Veritas/
├── 📁 .github/                          # GitHub workflows (preserved)
│   └── workflows/
│
├── 📁 pre-historic-legacy/              # ⬅️ ALL EXISTING CONTENT MOVED HERE
│   ├── ARCHIVE-MANIFEST.md              # Inventory of archived content
│   ├── MIGRATION-PLAN.md                # Migration strategy
│   ├── REVIEW-SCHEDULE.md               # Review timeline
│   │
│   ├── 📁 01-simulation-game/           # Godot 4 project
│   ├── 📁 02-website/                   # Static marketing site
│   ├── 📁 03-shared/                    # Monorepo shared code
│   │   ├── apps/
│   │   ├── axiom-esports-data/
│   │   └── packages/
│   │
│   ├── 📁 04-tests/                     # Integration tests
│   ├── 📁 05-legacy-docs/               # All current root-level docs
│   │   ├── AGENTS.md
│   │   ├── ARCHITECTURE.md
│   │   ├── CRIT_REPORT.md
│   │   └── ... (all .md files)
│   │
│   └── 📄 file_index.json               # Machine-readable inventory
│
├── 📁 context/                          # ⬅️ NEW: Agent context injection
│   ├── SYSTEM-IDENTITY.md               # Who this agent is
│   ├── USER-PROFILE.md                  # Who we're helping
│   ├── PROJECT-TENET.md                 # eSports-EXE architecture
│   ├── MEMORY-STATE.md                  # Current session state
│   └── CONSTRAINTS.md                   # Hard rules & limitations
│
├── 📁 frameworks/                       # ⬅️ NEW: Methodologies
│   ├── 1235-REVIEW/                     # Review protocol
│   │   ├── template.md
│   │   └── checklist.md
│   │
│   ├── AGENT-COORDINATION/              # Multi-agent patterns
│   │   ├── color-protocol.md            # [#TEA], [#ORG] usage
│   │   ├── handoff-procedure.md
│   │   └── conflict-resolution.md
│   │
│   ├── DESIGN-SYSTEM/                   # Visual specifications
│   │   ├── visual-spec-v3.md
│   │   ├── reference-images.md
│   │   └── component-library/
│   │
│   └── WIREFRAME-PROTOCOL/              # UI/UX standards
│       ├── quadrant-modularity.md
│       ├── zero-scroll-principle.md
│       └── sharp-corner-mandate.md
│
├── 📁 tools/                            # ⬅️ NEW: Agent tooling
│   ├── 📁 prompts/                      # Ready-to-use prompts
│   │   ├── 01-wireframe-generation.md
│   │   ├── 02-code-review.md
│   │   ├── 03-component-creation.md
│   │   └── 04-deployment-pipeline.md
│   │
│   ├── 📁 templates/                    # Document templates
│   │   ├── CRIT-report.md
│   │   ├── 1235-review.md
│   │   └── ADR-template.md
│   │
│   └── 📁 scripts/                      # Utility scripts
│       ├── validate-design.sh
│       └── check-constraints.py
│
├── 📁 roles/                            # ⬅️ NEW: Agent role definitions
│   ├── 01-ARCHITECT.md                  # System design agent
│   ├── 02-IMPLEMENTER.md                # Code generation agent
│   ├── 03-CRITIC.md                     # Review & critique agent
│   ├── 04-COORDINATOR.md                # Multi-agent orchestrator
│   └── 05-DEPLOYER.md                   # DevOps agent
│
├── 📁 active/                           # ⬅️ NEW: Current development
│   ├── 📁 sprint-current/               # Active sprint work
│   ├── 📁 wireframes-v3/                # Current wireframe iteration
│   └── 📁 experiments/                  # Spikes & prototypes
│
├── 📁 deliverables/                     # ⬅️ NEW: Completed outputs
│   ├── 📁 wireframes-v1/                # Historical versions
│   ├── 📁 wireframes-v2/
│   └── 📁 releases/                     # Tagged releases
│
└── 📄 README.md                         # Main entry point (rewritten)
```

---

## MIGRATION PLAN (pre-historic-legacy/)

### Phase 1: Archive (Immediate)
```bash
# Create archive structure
mkdir -p pre-historic-legacy/{01-simulation-game,02-website,03-shared,04-tests,05-legacy-docs}

# Move existing folders
mv simulation-game/ pre-historic-legacy/01-simulation-game/
mv website/ pre-historic-legacy/02-website/
mv shared/ pre-historic-legacy/03-shared/
mv tests/ pre-historic-legacy/04-tests/

# Move all root .md files to legacy docs
mv *.md pre-historic-legacy/05-legacy-docs/

# Preserve GitHub workflows (stay at root)
# .github/workflows/ remains
```

### Phase 2: Review (Week 1-2)
- Inventory all archived content
- Tag items: [KEEP], [MIGRATE], [DEPRECATE], [ARCHIVE]
- Create migration tickets for [MIGRATE] items

### Phase 3: Migration (Week 3-4)
- Move [MIGRATE] items to new structure
- Rewrite [KEEP] items for new context
- Document [DEPRECATE] decisions

### Phase 4: Cleanup (Week 5)
- Remove pre-historic-legacy/ if fully migrated
- Or maintain as historical reference

---

## CONTEXT FOLDER (INJECTION PROTOCOL)

Each agent session starts by reading these files in order:

```
1. context/SYSTEM-IDENTITY.md      → "Who am I?"
2. context/USER-PROFILE.md         → "Who am I helping?"
3. context/PROJECT-TENET.md        → "What are we building?"
4. context/MEMORY-STATE.md         → "Where are we?"
5. context/CONSTRAINTS.md          → "What can't I do?"
```

This ensures every agent has full context without repeating in prompts.

---

## FRAMEWORKS FOLDER (METHODOLOGY)

### 1235-REVIEW/
Standardized review protocol for all deliverables.

### AGENT-COORDINATION/
Color-coded communication system:
- [#TEA] Teal → Analysis, documentation
- [#ORG] Orange → Implementation, action
- [#GRN] Green → Success, completion
- [#RED] Red → Error, blockers

### DESIGN-SYSTEM/
Visual specifications enforced across all wireframes.

### WIREFRAME-PROTOCOL/
Specific rules: zero-scroll, sharp corners, quadrant modularity.

---

## TOOLS FOLDER (PROMPTS & TEMPLATES)

Pre-written prompts optimized for Kimi agents (1 token per response).

---

## ROLES FOLDER (AGENT PERSONAS)

Define 5 specialized agent types for different tasks.
Each role includes:
- Purpose statement
- Allowed actions
- Forbidden actions
- Communication style
- Success criteria

---

## ACTIVE FOLDER (CURRENT WORK)

Only current sprint items live here.
Cleaned after each milestone.

---

## DELIVERABLES FOLDER (COMPLETED)

Versioned outputs for reference and rollback.

---

## IMPLEMENTATION CHECKLIST

- [ ] Rename repository to `Satire-deck-Veritas`
- [ ] Create folder structure
- [ ] Move existing content to `pre-historic-legacy/`
- [ ] Create `ARCHIVE-MANIFEST.md`
- [ ] Create `MIGRATION-PLAN.md`
- [ ] Create `REVIEW-SCHEDULE.md`
- [ ] Write new root `README.md`
- [ ] Populate `context/` folder
- [ ] Populate `frameworks/` folder
- [ ] Populate `tools/prompts/` folder
- [ ] Define `roles/` agents
- [ ] Git commit with clear message
- [ ] Push to origin

---

Plan Version: 1.0.0
Created: 2026-03-31
Status: Ready for Implementation
