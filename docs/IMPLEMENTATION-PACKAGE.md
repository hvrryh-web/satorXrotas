# Satire-deck-Veritas: Implementation Package
## Complete Repository Reorganization & Agent Optimization

---

## DELIVERABLES SUMMARY

This package contains complete reorganization plans and optimized tooling for the `satorXrotas` → `Satire-deck-Veritas` migration.

---

## 1. REPOSITORY RESTRUCTURE PLAN

**File:** `docs/REPOSITORY-RESTRUCTURING-PLAN.md`

### New Structure:
```
Satire-deck-Veritas/
├── 📁 pre-historic-legacy/     # All existing content archived
│   ├── ARCHIVE-MANIFEST.md
│   ├── MIGRATION-PLAN.md
│   └── REVIEW-SCHEDULE.md
├── 📁 context/                  # Agent context injection
├── 📁 frameworks/               # Methodologies & standards
├── 📁 tools/                    # Prompts & templates
├── 📁 roles/                    # Agent definitions
├── 📁 active/                   # Current sprint work
└── 📁 deliverables/             # Completed outputs
```

### Migration Phases:
1. **Phase 1:** Archive existing content (Week 1)
2. **Phase 2:** Review and tag items (Week 1-2)
3. **Phase 3:** Migrate active items (Week 3-4)
4. **Phase 4:** Cleanup and finalize (Week 5)

---

## 2. AGENT ROLES (3 Defined)

### IMPLEMENTER [#ORG]
**File:** `docs/roles/02-IMPLEMENTER.md`
- Builds exactly to specification
- No creative interpretation
- Validates before delivery

### CRITIC [#RED]
**File:** `docs/roles/03-CRITIC.md`
- Harsh, honest evaluation
- Rejects anything not to spec
- Provides specific fix instructions

### (Additional roles: ARCHITECT, COORDINATOR, DEPLOYER - stubbed)

---

## 3. OPTIMIZED PROMPTS (1 Token Per Response)

### Prompt 1: Wireframe Generation
**File:** `docs/tools/prompts/01-wireframe-generation.md`

```
AGENT: IMPLEMENTER [#ORG]
TASK: TENET Portal Wireframe v3

SPEC (STRICT):
├── Background: #0A0A0A
├── Border-radius: 0px (ALL elements)
├── 4 HUB tiles: 280×320px, 2×2 grid
├── 2 Game tiles: 360×200px
├── ZERO feature cards
└── Color rules: [TEA] data, [ORG] CTAs

VALIDATE BEFORE SUBMIT:
[ ] 0px radius everywhere
[ ] Exactly 4 HUB tiles
[ ] Zero feature cards

OUTPUT: Single HTML file, inline CSS.
```

### Prompt 2: Code Review
**File:** `docs/tools/prompts/02-code-review.md`

Validation matrix format for systematic review.

---

## 4. CONTEXT INJECTION FILES

### SYSTEM-IDENTITY.md
Who the agent is, capabilities, constraints.

### USER-PROFILE.md
Eli's preferences, design taste, expectations.

### PROJECT-TENET.md
Architecture, 4 HUBs, current sprint status.

### CONSTRAINTS.md
Hard rules that cannot be broken.

---

## 5. FRAMEWORKS DEFINED

### 1235-REVIEW/
Standardized review protocol:
- 1 Report
- 2 Deliverables
- 3 Recommendations (with 5 sub-bullets each)

### AGENT-COORDINATION/
Color protocol for multi-agent communication:
- [#TEA] Analysis
- [#ORG] Implementation
- [#RED] Critique
- [#GRN] Coordination
- [#KIM] Framework

### DESIGN-SYSTEM/
Component analysis from StandardGT, Cirridae, Awwwards:
- Sharp corners (0px radius)
- 8px spacing scale
- 56px table rows
- Vignette masks
- Mobile-first

---

## 6. VISUAL SPECIFICATION V3

**File:** `docs/design-system/visual-specification-v3.md`

### Strict Rules:
- **Border Radius:** 0px default, 4px max
- **Colors:** 
  - #14B8A6 (TEAL) → Data only
  - #F97316 (ORG) → Buttons only
  - #FF4655 (RED) → LIVE badge only
- **Layout:** 4 HUB tiles, 2×2 grid, zero scroll
- **Typography:** Inter + JetBrains Mono

---

## 7. WEB DESIGN COMPONENTS TABLE

**File:** `docs/frameworks/DESIGN-SYSTEM/component-analysis.md`

Comparative analysis of:
- StandardGT
- Cirridae CSS
- Awwwards SOTD sites
- HLTV/VLR.gg

**Key Finding:** Premium sites use **0px border-radius**, sharp edges, minimal decoration.

---

## IMPLEMENTATION CHECKLIST

- [ ] Rename GitHub repo to `Satire-deck-Veritas`
- [ ] Create folder structure
- [ ] Move existing content to `pre-historic-legacy/`
- [ ] Create ARCHIVE-MANIFEST.md
- [ ] Populate `context/` folder (4 files)
- [ ] Populate `frameworks/` folder (3 subfolders)
- [ ] Populate `tools/prompts/` folder (2 prompts)
- [ ] Define `roles/` (2 complete, 3 stubs)
- [ ] Git commit all changes
- [ ] Push to origin

---

## USAGE INSTRUCTIONS

### For New Agent Sessions:

1. **Give agent context files first:**
   ```
   Read these files in order:
   1. context/SYSTEM-IDENTITY.md
   2. context/USER-PROFILE.md
   3. context/PROJECT-TENET.md
   4. context/CONSTRAINTS.md
   ```

2. **Then give optimized prompt:**
   ```
   Copy/paste from tools/prompts/01-wireframe-generation.md
   ```

3. **Agent will respond with:**
   - Color identifier [#ORG]
   - Validation checklist
   - Deliverable file

4. **Route to CRITIC:**
   ```
   [TO: #RED] Review this deliverable
   ```

---

## NEXT STEPS

1. **Immediate:** Rename repository, commit this structure
2. **Week 1:** Archive legacy content, create manifests
3. **Week 2:** Test agent workflows with new prompts
4. **Week 3:** Begin wireframe v3 implementation
5. **Ongoing:** Refine prompts based on results

---

Package Version: 1.0.0
Created: 2026-03-31
Status: Ready for Implementation
