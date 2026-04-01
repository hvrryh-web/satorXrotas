# REVIEW-SCHEDULE.md

## Archived Content Review Schedule

**Archive Location:** `pre-historic-legacy/`
**Review Coordinator:** CRITIC Agent
**Schedule Version:** 1.0.0

---

## Week 1 (2026-04-01 - 2026-04-07)

### Focus: Archive Stabilization
- [ ] Verify all content moved correctly
- [ ] Validate `ARCHIVE-MANIFEST.md` accuracy
- [ ] Test new folder structure
- [ ] Git commit and push

### Deliverables:
- Archive manifest validated
- New structure functional
- Team (agents) trained on new layout

---

## Week 2 (2026-04-08 - 2026-04-14)

### Focus: Critical Migration (03-shared/)
**Item:** `pre-historic-legacy/03-shared/`
**Tag:** [MIGRATE] CRITICAL

### Tasks:
- [ ] Audit `03-shared/` contents
- [ ] Identify reusable components
- [ ] Create migration plan to `active/sprint-current/`
- [ ] Execute migration
- [ ] Verify functionality post-migration

### Success Criteria:
- TENET architecture functional in new location
- All imports/exports working
- Build passes

---

## Week 3 (2026-04-15 - 2026-04-21)

### Focus: Design System Extraction
**Item:** `pre-historic-legacy/02-website/design-system/`
**Tag:** [MIGRATE] HIGH

### Tasks:
- [ ] Review design system components
- [ ] Compare with `frameworks/DESIGN-SYSTEM/`
- [ ] Extract unique/valuable components
- [ ] Integrate into current design system
- [ ] Document changes

---

## Week 4 (2026-04-22 - 2026-04-30)

### Focus: Legacy Documentation Review
**Item:** `pre-historic-legacy/05-legacy-docs/`
**Tag:** [DEPRECATE] + [KEEP]

### Tasks:
- [ ] Review each `.md` file
- [ ] Tag: [KEEP] for valuable content → Rewrite
- [ ] Tag: [DEPRECATE] for outdated content → Document and remove
- [ ] Create summary of decisions

### Files to Review:
- AGENTS.md
- ARCHITECTURE.md
- CHANGELOG.md
- CONTRIBUTING.md
- CRIT_REPORT.md
- DEPLOYMENT_ARCHITECTURE.md
- DEPLOYMENT_CHECKLIST.md
- DESIGN_GAP_ANALYSIS.md
- DESIGN_OVERVIEW.md
- REPOSITORY_CHANGES.md
- REPOSITORY_TRANSFER_GUIDE.md
- SKILL_ARCHITECTURE_ANALYSIS.md

---

## Month 2 (2026-05-01 - 2026-05-31)

### Focus: Archive Cleanup Decision

### Options:
1. **Keep Archive** - Maintain as historical reference
   - Update `ARCHIVE-MANIFEST.md` quarterly
   - Keep in repository

2. **Delete Archive** - Remove migrated content
   - Only if confident all value extracted
   - Create final archive snapshot

### Decision Required By: 2026-05-15

---

## Review Process

### For Each Review:
1. **IMPLEMENTER** audits contents
2. **CRITIC** evaluates value/priority
3. **ARCHITECT** decides migration approach
4. **COORDINATOR** schedules work
5. **DEPLOYER** executes (if applicable)

### Output Format:
```markdown
## Review: [Item Name]
**Date:** YYYY-MM-DD
**Reviewer:** [Agent]
**Decision:** [MIGRATE | KEEP | DEPRECATE | ARCHIVE]
**Priority:** [CRITICAL | HIGH | MEDIUM | LOW]
**Action:** [Description]
**Notes:** [Additional context]
```

---

*Schedule subject to adjustment based on sprint priorities.*
