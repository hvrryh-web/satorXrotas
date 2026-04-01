# Satire-Deck-Veritas Organizational Index
## Master Directory Structure & Navigation

---

## ROOT STRUCTURE

```
Satire-deck-Veritas/
├── 📁 .github/                          # GitHub workflows (preserved)
│
├── 📁 pre-historic-legacy/              # Archived content
│   ├── ARCHIVE-MANIFEST.md
│   ├── MIGRATION-PLAN.md
│   ├── REVIEW-SCHEDULE.md
│   └── [legacy content folders]
│
├── 📁 context/                          # Agent context injection
│   ├── SYSTEM-IDENTITY.md
│   ├── USER-PROFILE.md
│   ├── PROJECT-TENET.md
│   ├── CONSTRAINTS.md
│   └── INDEX.md
│
├── 📁 frameworks/                       # Methodologies & standards
│   ├── 1235-REVIEW/
│   ├── AGENT-COORDINATION/
│   ├── DESIGN-SYSTEM/
│   └── WIREFRAME-PROTOCOL/
│
├── 📁 tools/                            # Agent tooling
│   ├── prompts/
│   ├── templates/
│   └── scripts/
│
├── 📁 roles/                            # Agent definitions
│   ├── 01-ARCHITECT.md
│   ├── 02-IMPLEMENTER.md
│   ├── 03-CRITIC.md
│   ├── 04-COORDINATOR.md
│   └── 05-DEPLOYER.md
│
├── 📁 active/                           # Current development
│   ├── sprint-current/
│   ├── wireframes-v3/
│   └── experiments/
│
├── 📁 deliverables/                     # Completed outputs
│   ├── wireframes-v1/
│   ├── wireframes-v2/
│   └── releases/
│
├── 📁 operations/                       # [NEW] Daily operations
│   ├── to-do-lists/
│   ├── plans/
│   ├── satire-journal/
│   │   └── 2026/
│   │       └── 04-April/
│   │           ├── week-01/
│   │           │   ├── start-of-week.md
│   │           │   ├── end-of-week.md
│   │           │   ├── week-report.md
│   │           │   └── daily/
│   │           │       ├── 2026-04-01.md
│   │           │       └── [daily entries]
│   │           └── week-[XX]/
│   └── notebooks/
│
├── 📁 shrine/                           # [NEW] Presentation to user
│   ├── INDEX.md
│   ├── ready-for-review/
│   ├── approved/
│   └── archived/
│
├── 📁 sator/                            # [NEW] Products & frameworks
│   ├── INDEX.md
│   ├── confirmed/
│   ├── unconfirmed/
│   ├── rejected/
│   └── adaptions/
│
├── 📁 reviews/                          # [NEW] Review checkpoints
│   ├── eSports-EXE/
│   ├── user-review/
│   └── checkpoints/
│
├── 📁 docs/                             # Documentation
│   ├── master-plan/
│   ├── adrs/
│   ├── design-system/
│   ├── roadmap/
│   ├── references/
│   └── reviews/
│
├── 📁 visual-assets/                    # [NEW] Art & diagrams
│   ├── diagrams/
│   ├── wireframes/
│   └── exports/
│
├── 📁 css-components/                   # [NEW] Production CSS
│   ├── confirmed/
│   ├── in-development/
│   └── INDEX.md
│
├── 📁 webpage-components/               # [NEW] Production components
│   ├── confirmed/
│   ├── in-development/
│   └── INDEX.md
│
└── 📄 README.md                         # Main entry point
```

---

## FOLDER DESCRIPTIONS

### 🔴 CRITICAL PATH (Daily Use)
| Folder | Purpose | Update Frequency |
|--------|---------|------------------|
| `operations/to-do-lists/` | Active tasks | Continuous |
| `operations/satire-journal/` | Daily logs | Daily |
| `active/sprint-current/` | Current work | Per sprint |
| `shrine/ready-for-review/` | User presentation | As needed |

### 🟡 REFERENCE (Weekly Use)
| Folder | Purpose | Update Frequency |
|--------|---------|------------------|
| `context/` | Agent initialization | When roles change |
| `frameworks/` | Methodologies | When approved |
| `tools/prompts/` | Agent prompts | When optimized |
| `roles/` | Agent definitions | When updated |

### 🟢 ARCHIVE (Monthly Use)
| Folder | Purpose | Update Frequency |
|--------|---------|------------------|
| `pre-historic-legacy/` | Old content | Never (archive only) |
| `deliverables/releases/` | Tagged releases | Per milestone |
| `sator/rejected/` | Failed proposals | As needed |

---

## INDEX FILES

Every folder contains an `INDEX.md` file with:
1. Folder purpose description
2. Current item count
3. Last updated timestamp
4. Items list with status
5. Links to related folders

### Index Template
```markdown
# [FOLDER NAME] Index

**Purpose:** [One-line description]
**Last Updated:** [YYYY-MM-DD HH:MM]
**Item Count:** [N]

## Contents

| Item | Status | Date | Notes |
|------|--------|------|-------|
| [name] | [status] | [date] | [brief] |

## Quick Links
- Parent: [link]
- Related: [link]
- Next Review: [date]
```

---

## CONTEXT DRIFT PROTECTION

### Isolation Zones
```
┌────────────────────────────────────────────────────┐
│  ZONE 1: ACTIVE (operations/, active/)             │
│  └── High churn, daily updates                     │
├────────────────────────────────────────────────────┤
│  ZONE 2: REFERENCE (context/, frameworks/)         │
│  └── Stable, weekly updates                        │
├────────────────────────────────────────────────────┤
│  ZONE 3: ARCHIVE (pre-historic-legacy/)            │
│  └── Frozen, no updates                            │
├────────────────────────────────────────────────────┤
│  ZONE 4: OUTPUT (shrine/, deliverables/)           │
│  └── Append-only, user-facing                      │
└────────────────────────────────────────────────────┘
```

### Sync Protocol
1. **Daily:** Update operations/ folder
2. **Weekly:** Update satire-journal/week-report.md
3. **Monthly:** Archive old daily entries
4. **Quarterly:** Review sator/ categorizations

---

## NAMING CONVENTIONS

### Files
```
[TYPE]-[descriptive-name]-[version].[ext]

Examples:
- 1235-do-framework-v1.0.0.md
- wireframe-tenet-portal-v3.html
- PPT-appraisal-report.md
```

### Folders
```
[category]-[subcategory]/

Examples:
- to-do-lists/
- css-components/confirmed/
- satire-journal/2026/04-April/week-01/
```

### Daily Entries
```
YYYY-MM-DD.md

Example:
- 2026-04-01.md
```

---

## ACCESS PATTERNS

### For You (User)
```
Entry: shrine/INDEX.md
       ↓
Review: shrine/ready-for-review/
       ↓
Approve: Move to shrine/approved/
       ↓
Archive: Auto-move after 30 days
```

### For Me (Agent)
```
Startup: context/ → roles/ → frameworks/
       ↓
Work: operations/to-do-lists/ → active/
       ↓
Deliver: shrine/ready-for-review/
       ↓
Log: operations/satire-journal/
```

---

## CREATION STATUS

- [x] Folder structure defined
- [x] Index system specified
- [x] Naming conventions established
- [x] Context drift protection outlined
- [ ] Physical folders created (next step)
- [ ] Index files populated (next step)
- [ ] Git commit (final step)

---

Index Version: 1.0.0
Created: 2026-04-01
Status: SPECIFICATION COMPLETE — READY FOR IMPLEMENTATION
