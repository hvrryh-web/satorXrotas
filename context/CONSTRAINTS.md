# CONSTRAINTS.md

## Hard Rules & Limitations

**Version:** 1.0.0  
**Last Updated:** 2026-04-01  
**Applies To:** All agents working on Satire-deck-Veritas

---

## Technical Constraints

### Repository Structure
- **NEVER** modify `pre-historic-legacy/` without approval
- **ALWAYS** check new structure before creating files
- **MANDATORY** PowerShell compatibility for all scripts

### Code Standards
- Border radius: **0px** (sharp corners only)
- Maximum radius: **4px** for interactive elements
- Color [#TEA] (#14B8A6): **NEVER** for CTAs
- Color [#ORG] (#F97316): **NEVER** for stats/data
- HUB tiles: **EXACTLY 4** in 2×2 grid
- Feature cards on TENET portal: **ZERO**

### Git Workflow
- Commit messages: Imperative, descriptive, include scope
- No direct pushes to `main` without review
- All migrations require Windows user check

---

## Design Constraints

### Visual System (v3)
- Background: `#0F172A` (dark slate)
- ROTAS accent: `#14B8A6` (teal)
- OPERA accent: `#F97316` (orange)
- Text primary: `#F8FAFC`
- Text secondary: `#94A3B8`

### Layout Principles
- **Zero-scroll mandate** - All content visible without scroll
- **Quadrant modularity** - 2×2 grid system
- **Sharp corners** - No rounded edges
- **Progressive disclosure** - Casual → Aspiring → Professional views

---

## Process Constraints

### Agent Coordination
- **IMPLEMENTER** [#ORG]: Code generation only
- **CRITIC** [#RED]: Review and reject only
- **ARCHITECT**: System design only
- **COORDINATOR**: Multi-agent orchestration only

### Communication Protocol
- Use color tags in all agent responses
- Validate against constraints before delivering
- Reject work that violates hard rules

### Review Requirements
- 1235 Review Framework for all deliverables
- 1 Report, 2 Deliverables, 3 Recommendations
- Minimum score: 7/10 to pass, 9/10 to approve

---

## Migration Constraints

### To eSports-EXE (Migration Target)
- Component must be **feature-complete**
- All tests must **pass**
- Documentation must be **complete**
- Code review must be **approved**
- **PowerShell compatibility verified**
- **Windows user acceptance test passed**

### NEVER Migrate:
- Incomplete features
- Unreviewed code
- Unverified scripts
- Files with known issues

---

## Operational Constraints

### User Environment
- **OS:** Windows (PowerShell)
- **Shell:** PowerShell 5.1+
- **Path separator:** `\` (backslash)
- **Home directory:** `$env:USERPROFILE`

### Script Requirements
All automation must provide PowerShell equivalents:
- Directory creation: `New-Item -ItemType Directory`
- File copy: `Copy-Item`
- File move: `Move-Item`
- Path joining: `Join-Path`

---

## Forbidden Actions

- ❌ Modifying archived content without review
- ❌ Creating rounded corners (>4px)
- ❌ Using [#TEA] for buttons/CTAs
- ❌ Using [#ORG] for data displays
- ❌ Adding feature cards to TENET portal
- ❌ Using Unix-only commands in user-facing scripts
- ❌ Pushing to `main` without Windows check
- ❌ Migrating incomplete components to eSports-EXE

---

## Exception Process

If a constraint must be violated:
1. Document the reason
2. Get explicit approval from user
3. Tag with [#RED] and justification
4. Update this file with exception record

---

*Constraints are non-negotiable. They exist to maintain quality and consistency.*
