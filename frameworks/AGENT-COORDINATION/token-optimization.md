# Token Optimization Techniques for Agent Operations
## Research Summary & Implementation Guide

---

## EXECUTIVE SUMMARY

**Objective:** Maximize deliverable output while minimizing token consumption per agent response.

**Current Baseline:** 1 token per response for established chats
**Target:** Maintain quality with ≤400 tokens per response

---

## TECHNIQUE 1: STRUCTURED RESPONSE FORMATS

### Validation Matrix Pattern
```
┌─────────────┬──────────┬──────────┬────────┐
│ Check       │ Expected │ Actual   │ ✓/✗    │
├─────────────┼──────────┼──────────┼────────┤
│ [Item 1]    │ [value]  │ [value]  │ [ ]    │
│ [Item 2]    │ [value]  │ [value]  │ [ ]    │
└─────────────┴──────────┴──────────┴────────┘
```
**Token Savings:** ~30% vs. prose format
**Use Case:** Code reviews, specification validation

### Checklist Pattern
```
VALIDATION:
[✓] Item 1 complete
[✓] Item 2 complete
[✗] Item 3 failed
[ ] Item 4 pending
```
**Token Savings:** ~40% vs. sentence format
**Use Case:** Completion confirmation, status updates

### Color-Coded Status
```
[#TEA] Analysis complete
[#ORG] Implementation ready
[#RED] Blocker identified
[#GRN] Approved for delivery
```
**Token Savings:** ~20% vs. descriptive status
**Use Case:** Quick handoffs, status broadcasts

---

## TECHNIQUE 2: CONTEXT INJECTION EFFICIENCY

### File Reference Convention
**Inefficient:**
```
The file is located at /root/.openclaw/workspace/eSports-EXE/docs/design-system/visual-specification-v3.md and contains the specifications for...
```

**Optimized:**
```
SPEC: docs/design-system/visual-specification-v3.md
KEY POINTS:
- Background: #0A0A0A
- Radius: 0px
- Colors: [TEA] data, [ORG] CTAs
```

**Token Savings:** ~60% by omitting full paths and redundant prose

### Context File Priority Order
```
1. SYSTEM-IDENTITY.md      (essential)
2. USER-PROFILE.md         (essential)
3. PROJECT-TENET.md        (essential)
4. CONSTRAINTS.md          (essential)
5. [task-specific spec]    (as needed)
```
**Rule:** Never include more than 5 context files per prompt

---

## TECHNIQUE 3: PROMPT TEMPLATES

### Template Structure
```
AGENT: [ROLE] [COLOR]
TASK: [Brief description]

SPEC (STRICT):
├── Item 1: [value]
├── Item 2: [value]
└── Item 3: [value]

VALIDATE BEFORE SUBMIT:
[ ] Check 1
[ ] Check 2
[ ] Check 3

OUTPUT: [Expected format]
```

**Token Count:** ~80–120 tokens
**Effectiveness:** High precision, minimal back-and-forth

### One-Letter Commands
| Command | Meaning | Use Case |
|---------|---------|----------|
| `S` | Start/Begin | Initiate task |
| `C` | Check status | Progress inquiry |
| `X` | Stop/Pause | Halt execution |
| `R` | Review | Submit for critique |
| `A` | Approve | Confirm acceptance |
| `D` | Deliver | Final output |

---

## TECHNIQUE 4: COMPRESSION STRATEGIES

### Abbreviation Standards
| Full Term | Abbreviation | Context |
|-----------|--------------|---------|
| Border radius | `br` | CSS/styling |
| Background | `bg` | CSS/styling |
| Typography | `typo` | Design |
| Component | `comp` | Development |
| Specification | `spec` | Documentation |
| Deliverable | `deliv` | Project mgmt |

### Symbol Substitution
| Phrase | Symbol | Example |
|--------|--------|---------|
| Greater than | `>` | `> 10 reviews` |
| Less than | `<` | `< 4px` |
| Greater/equal | `≥` | `≥ 9/10` |
| Less/equal | `≤` | `≤ 400 tokens` |
| Checkmark | `✓` | `✓ Complete` |
| X mark | `✗` | `✗ Failed` |

---

## TECHNIQUE 5: BATCHING & CONSOLIDATION

### Single Turn Multi-Task
**Inefficient (3 turns):**
```
User: Create header component
Agent: [creates header]
User: Create footer component
Agent: [creates footer]
User: Create navigation
Agent: [creates nav]
```

**Optimized (1 turn):**
```
User: Create: 1) Header, 2) Footer, 3) Navigation
AGENT: [all 3 in single response]
```

**Token Savings:** ~50% by reducing context overhead

### Consolidated Validation
```
DELIVERABLES:
┌──────────┬────────┬──────────┐
│ File     │ Size   │ Status   │
├──────────┼────────┼──────────┤
│ 01.html  │ 17KB   │ ✓ PASS   │
│ 02.html  │ 25KB   │ ✓ PASS   │
│ 03.html  │ 18KB   │ ✗ FAIL   │
└──────────┴────────┴──────────┘
```

---

## TOKEN BUDGET GUIDELINES

### Per Response Targets
| Agent Type | Target Tokens | Max Tokens |
|------------|---------------|------------|
| IMPLEMENTER | 200–300 | 400 |
| CRITIC | 300–400 | 500 |
| COORDINATOR | 150–200 | 300 |
| GENERALIS | 250–350 | 450 |
| INTERFACE | 200–300 | 400 |
| STRUCTURA | 200–300 | 400 |

### Budget Allocation per Task
| Phase | % of Budget | Example (400 tokens) |
|-------|-------------|----------------------|
| Context | 10% | 40 tokens |
| Implementation | 50% | 200 tokens |
| Validation | 20% | 80 tokens |
| Status/Handoff | 20% | 80 tokens |

---

## IMPLEMENTATION CHECKLIST

- [ ] Create abbreviation glossary
- [ ] Establish color protocol
- [ ] Design validation matrices
- [ ] Configure one-letter commands
- [ ] Train agents on compression
- [ ] Monitor token usage per session
- [ ] Optimize context file sizes
- [ ] Create template library

---

## MEASUREMENT & TRACKING

### Token Log Format
```json
{
  "session_id": "[uuid]",
  "timestamp": "2026-04-01T00:00:00Z",
  "agent": "IMPLEMENTER",
  "task": "wireframe-v3",
  "tokens_in": 120,
  "tokens_out": 280,
  "efficiency_score": 0.93
}
```

### Efficiency Targets
| Metric | Target | Current |
|--------|--------|---------|
| Avg tokens/response | ≤350 | TBD |
| Tasks per turn | ≥2 | TBD |
| Back-and-forth ratio | ≤1.2 | TBD |
| Context reuse % | ≥70% | TBD |

---

Guide Version: 1.0.0
Last Updated: 2026-04-01
Status: ACTIVE — APPLY TO ALL AGENT OPERATIONS
