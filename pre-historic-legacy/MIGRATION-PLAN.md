# MIGRATION-PLAN.md

## Repository Restructure Migration Plan

**From:** satorXrotas (flat structure)
**To:** Satire-deck-Veritas (organized hierarchy)
**Started:** 2026-04-01
**Target Completion:** 2026-04-30

---

## Phase 1: Archive (COMPLETE)
**Date:** 2026-04-01
**Status:** ✅ DONE

### Actions Taken:
- [x] Created `pre-historic-legacy/` structure
- [x] Moved `simulation-game/` → `pre-historic-legacy/01-simulation-game/`
- [x] Moved `website/` → `pre-historic-legacy/02-website/`
- [x] Moved `shared/` → `pre-historic-legacy/03-shared/`
- [x] Moved `tests/` → `pre-historic-legacy/04-tests/`
- [x] Moved `legacy/` → `pre-historic-legacy/05-legacy-docs/`
- [x] Moved root `.md` files → `pre-historic-legacy/05-legacy-docs/`
- [x] Created `ARCHIVE-MANIFEST.md`

### Files Archived: 33 items, ~53MB

---

## Phase 2: New Structure (COMPLETE)
**Date:** 2026-04-01
**Status:** ✅ DONE

### Actions Taken:
- [x] Created `context/` folder
- [x] Created `frameworks/` folder with subdirectories
- [x] Created `tools/` folder with subdirectories
- [x] Created `roles/` folder
- [x] Created `active/` folder with subdirectories
- [x] Created `deliverables/` folder with subdirectories
- [x] Migrated `docs/context/` → `context/`
- [x] Migrated `docs/frameworks/` → `frameworks/`
- [x] Migrated `docs/roles/` → `roles/`
- [x] Migrated `docs/tools/prompts/` → `tools/prompts/`
- [x] Migrated `docs/design-system/` → `frameworks/DESIGN-SYSTEM/`

---

## Phase 3: Documentation (IN PROGRESS)
**Date:** 2026-04-01
**Status:** 🔄 ACTIVE

### Actions Required:
- [ ] Create `context/CONSTRAINTS.md`
- [ ] Create `context/MEMORY-STATE.md`
- [ ] Create `frameworks/WIREFRAME-PROTOCOL/` documents
- [ ] Create `tools/templates/`
- [ ] Create `tools/scripts/`
- [ ] Write new root `README.md`
- [ ] Create `REVIEW-SCHEDULE.md`

---

## Phase 4: Migration to Active (PENDING)
**Date:** 2026-04-08
**Status:** ⏸️ PENDING

### Items to Migrate:
1. `pre-historic-legacy/03-shared/` → `active/sprint-current/`
   - Contains working TENET architecture
   - Priority: CRITICAL

2. `pre-historic-legacy/02-website/design-system/` → `frameworks/DESIGN-SYSTEM/`
   - Extract reusable components
   - Priority: HIGH

---

## Phase 5: Cleanup (PENDING)
**Date:** 2026-05-01
**Status:** ⏸️ PENDING

### Actions:
- [ ] Review all `pre-historic-legacy/` contents
- [ ] Remove items tagged [DEPRECATE]
- [ ] Update `ARCHIVE-MANIFEST.md`
- [ ] Decide: Keep archive or delete?

---

## PowerShell Compatibility

All migration operations documented with PowerShell equivalents.
See: `RESTRUCTURE-IMPLEMENTATION.md`

---

*Last Updated: 2026-04-01*
