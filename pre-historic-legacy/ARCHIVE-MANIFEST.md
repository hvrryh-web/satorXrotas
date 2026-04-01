# ARCHIVE-MANIFEST.md

## pre-historic-legacy/ Contents

Generated: 2026-04-01
Migration Phase: Initial Archive

---

### 01-simulation-game/
**Source:** Root `simulation-game/`
**Contents:** Godot 4 tactical FPS simulation project
- Defs/ - Type definitions
- maps/ - Game maps
- scenes/ - Godot scenes
- scripts/ - GDScript files
- tactical-fps-sim-core-updated/ - Core simulation logic
- project.godot - Project configuration
- icon.svg - Project icon

**Status:** ARCHIVE - Godot simulation preserved for reference
**Migration Decision:** Review for reusable components

---

### 02-website/
**Source:** Root `website/`
**Contents:** Static marketing website
- config/
- data/
- design-system/
- ARCHITECTURE.md
- CHANGELOG.md
- CONTRIBUTING.md
- DATA_ARCHITECTURE.md

**Status:** ARCHIVE - Marketing site preserved
**Migration Decision:** Review design system components for reuse

---

### 03-shared/
**Source:** Root `shared/`
**Contents:** Monorepo shared packages
- api/ - API definitions
- apps/ - Application code
- axiom-esports-data/ - Data layer (14 subdirectories)
- docs/ - Documentation
- packages/ - Shared packages (components, configs, types, utils)

**Status:** ARCHIVE - Core monorepo code
**Migration Decision:** CRITICAL - Contains working TENET architecture

---

### 04-tests/
**Source:** Root `tests/`
**Contents:** Integration tests
- integration/ - Test suites

**Status:** ARCHIVE
**Migration Decision:** Review for test patterns

---

### 05-legacy-docs/
**Source:** Root `*.md` files
**Contents:** Historical documentation
- AGENTS.md
- ARCHITECTURE.md
- CHANGELOG.md
- CONTRIBUTING.md
- CRIT_REPORT.md
- DEPLOYMENT_ARCHITECTURE.md
- DEPLOYMENT_CHECKLIST.md
- DESIGN_GAP_ANALYSIS.md
- DESIGN_OVERVIEW.md
- README.md (original)
- REPOSITORY_CHANGES.md
- REPOSITORY_TRANSFER_GUIDE.md
- SKILL_ARCHITECTURE_ANALYSIS.md

**Status:** ARCHIVE - Reference documentation
**Migration Decision:** Review for reusable content

---

## Inventory Statistics

| Category | Items | Size |
|----------|-------|------|
| Simulation Game | 7 entries | ~2MB |
| Website | 7 entries | ~500KB |
| Shared (Monorepo) | 5 entries | ~50MB |
| Tests | 1 entry | ~100KB |
| Legacy Docs | 13 files | ~200KB |
| **TOTAL** | **33 items** | **~53MB** |

---

## Review Schedule

| Item | Review By | Action |
|------|-----------|--------|
| 03-shared/ | 2026-04-08 | MIGRATE to active/ |
| 02-website/design-system | 2026-04-15 | EXTRACT to frameworks/DESIGN-SYSTEM/ |
| 01-simulation-game | 2026-04-30 | ARCHIVE (no migration) |
| 05-legacy-docs | 2026-05-01 | REVIEW and DEPRECATE |

---

## Migration Tags

- [MIGRATE] - Move to new structure
- [KEEP] - Rewrite for new context
- [DEPRECATE] - Document and remove
- [ARCHIVE] - Preserve as reference

---

*This manifest is machine-readable. Do not edit manually without updating the review schedule.*
