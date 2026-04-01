# Agent Coordination Color Protocol
## Communication Standards for Multi-Agent Systems

---

## COLOR IDENTIFIERS

Every agent response must begin with color identifier:

| Color | Code | Agent Role | Usage |
|-------|------|------------|-------|
| [#TEA] | #14B8A6 | ANALYST | Analysis, documentation, review |
| [#ORG] | #F97316 | IMPLEMENTER | Implementation, coding, building |
| [#RED] | #EF4444 | CRITIC | Review, rejection, violations |
| [#GRN] | #22C55E | COORDINATOR | Success, approval, completion |
| [#BLU] | #3B82F6 | DEPLOYER | DevOps, deployment, infrastructure |
| [#KIM] | #00D4AA | FRAMEWORK | Meta-communication, system |

---

## MESSAGE FORMAT

```
[#COLOR] Brief context
[CONTENT]
[DELIVERABLE/SUMMARY]
```

---

## HANDOFF PROTOCOL

### IMPLEMENTER → CRITIC
```
[#ORG] TENET Portal v3 complete

VALIDATION: 7/7 passed
FILE: 01-tenet-portal.html
SIZE: 17KB

[TO: #RED] Ready for CRIT
```

### CRITIC → COORDINATOR (Approve)
```
[#RED] TENET Portal v3 reviewed

SCORE: 9.2/10 → APPROVED
VIOLATIONS: 0

[TO: #GRN] Ready for user review
```

### CRITIC → IMPLEMENTER (Revise)
```
[#RED] TENET Portal v3 reviewed

SCORE: 6.5/10 → REJECTED
VIOLATIONS:
1. Line 23: radius 16px → 0px
2. Line 45: orange on stats → teal

[TO: #ORG] Fix required
```

### COORDINATOR → USER
```
[#GRN] TENET Portal v3 approved

QUALITY: 9.2/10
STATUS: Ready for your review

[TO: USER] Awaiting feedback
```

---

## CONFLICT RESOLUTION

When agents disagree:

```
[#KIM] CONFLICT RESOLUTION

ISSUE: [description]
AGENT A [#TEA]: [position]
AGENT B [#ORG]: [position]

RESOLUTION: [decision]
REASON: [rationale]
```

User has final authority.

---

## STATUS BROADCASTS

```
[#KIM] SYSTEM STATUS

ACTIVE AGENTS: 3
TASK QUEUE: 2 pending
CURRENT: TENET Portal v3 (IMPLEMENTER)
BLOCKERS: None
```

---

## COLOR COMBINATIONS

| Combination | Meaning |
|-------------|---------|
| [#TEA] → [#ORG] | Spec handoff to implementation |
| [#ORG] → [#RED] | Implementation to review |
| [#RED] → [#ORG] | Rejection, return to implementer |
| [#RED] → [#GRN] | Approval to coordinator |
| [#GRN] → [USER] | Completion, user review |
| [#KIM] | Meta/system messages |

---

Protocol Version: 1.0.0
Last Updated: 2026-03-31
