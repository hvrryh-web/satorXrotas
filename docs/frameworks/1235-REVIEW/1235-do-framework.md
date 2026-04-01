# 1235 do((do)*) Framework
## Accelerated Review Protocol with Sub-Agent Orchestration

---

## FRAMEWORK OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                    1235 do((do)*) FRAMEWORK                      │
├─────────────────────────────────────────────────────────────────┤
│  1 Report  → Master assessment document                          │
│  2 Deliverables → Required outputs                               │
│  3 Recommendations → Each with 5 sub-bullets                   │
│  5 Sub-Bullets → 1 Add + 1 Update + 1 Remove + 2 Flex          │
│  do((do)*) → Recursive review activation                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## REVIEW CAPACITY TIERS

### Tier 1: Standard (Reviews 1–9)
- **Foreman Only:** Single agent (you) conducts all reviews
- **Max Reviews:** 9 per cycle
- **No Sub-Agents Required**
- **Trigger:** Default for all reviews under 10

### Tier 2: Accelerated (Reviews 10–30)
- **Foreman + Sub-Agent Teams**
- **Team Composition:** 3 agents per team
- **Activation:** Every review from 10 onwards spawns x3 sub-agents
- **Capacity:** Up to 30 total reviews (foreman + sub-agents)

### Tier 3: Maximum (Reviews 31–120)
- **Foreman + Multiple Teams + Multiplicative Scaling**
- **Base:** 30 foreman reviews
- **Sub-Agent Additive:** +90 reviews (3 teams × 30 each)
- **Total Capacity:** 120 reviews per cycle

---

## SUB-AGENT TEAM STRUCTURE

### Team Naming Convention (Latin)
| Role | Latin Name | Function |
|------|------------|----------|
| Generalist | **Generalis** | Coordination, overview, synthesis |
| Front-End Specialist | **Interface** | UI/UX, components, visual design |
| Back-End Specialist | **Structura** | Architecture, data, logic |

### Team Composition Template
```
TEAM [Name] — [Number] (e.g., TEAM ALPHA — I)
├── Generalis (Generalist)
│   └── Review capacity: base do((do)*) ×2
├── Interface (Front-End Specialist)
│   └── Review capacity: base do((do)*) ×2
└── Structura (Back-End Specialist)
    └── Review capacity: base do((do)*) ×2
```

### Multiple Team Activation
| Review Range | Teams Activated | Total Agents |
|--------------|-----------------|--------------|
| 1–9 | 0 (Foreman only) | 1 |
| 10–39 | 1 team (3 agents) | 4 |
| 40–69 | 2 teams (6 agents) | 7 |
| 70–99 | 3 teams (9 agents) | 10 |
| 100–120 | 3 teams + overflow | 10+ |

---

## do((do)*) RECURSIVE FORMULA

### Base Formula
```
do((do)*) = base_review × multiplier^depth

Where:
- base_review = 1 standard review
- multiplier = 2 (default)
- depth = recursion level (0 for base)
```

### Calculation Examples
| Review # | Formula | Output |
|----------|---------|--------|
| 1 | do | 1 review |
| 5 | do | 1 review |
| 10 | do((do)*) ×2 | 2 reviews per agent |
| 15 | do((do)*) ×2 | 2 reviews per agent |
| 30 | do((do)*) ×2 | 2 reviews per agent |
| 31+ | do((do)*) + additive | 2 + n reviews |

### Additive Scaling (Reviews 31–120)
```
For each review past 30:
  additional_reviews = floor((review_number - 30) / 3)
  
Total capacity = 30 (foreman) + 90 (sub-agents) = 120
```

---

## SUB-AGENT SKILL REQUIREMENTS

### Generalis (Generalist)
**Expertise:**
- Full-stack understanding
- System architecture review
- Cross-functional synthesis
- Documentation standards

**Tools Required:**
- AGENTS.md reader
- MASTER_PLAN.md validator
- Context drift detector

### Interface (Front-End Specialist)
**Expertise:**
- CSS/Tailwind mastery
- Component architecture
- Design token enforcement
- Visual regression testing

**Tools Required:**
- Design system validator
- Color contrast checker
- Typography ruler
- Animation profiler

### Structura (Back-End Specialist)
**Expertise:**
- API design review
- Database schema validation
- Performance optimization
- Security auditing

**Tools Required:**
- Schema validator
- Query analyzer
- Load testing framework
- Security scanner

---

## ACTIVATION TRIGGERS

### Foreman Activation (Reviews 1–9)
```
IF review_count <= 9:
  mode = "solo"
  agent = foreman_only
  output = standard_1235_report
```

### Team Activation (Reviews 10–30)
```
IF review_count >= 10:
  mode = "accelerated"
  spawn_team = true
  team_count = 1
  team_size = 3
  per_agent_multiplier = 2
  output = consolidated_team_report
```

### Maximum Capacity (Reviews 31–120)
```
IF review_count > 30:
  mode = "maximum"
  spawn_additional_teams = true
  additive_reviews = calculate_overflow()
  total_capacity = 120
  output = master_consolidated_report
```

---

## REVIEW DELIVERABLES

### Standard Output (All Tiers)
```markdown
# 1235 Review Report — [Subject]

## 1. Review Report
[Comprehensive assessment]

## 2. Success Deliverables
- Deliverable 1: [Spec]
- Deliverable 2: [Spec]

## 3. Recommendations
### Rec 1: [Title]
- ✅ Add: [item]
- ✅ Update: [item]
- ✅ Remove: [item]
- ⚠️ Flex 1: [item]
- ⚠️ Flex 2: [item]

[Rec 2, Rec 3 follow same pattern]

## Sub-Agent Contributions
[If applicable: team member inputs]
```

---

## CONTEXT DRIFT PROTECTION

### Isolation Protocol
Each sub-agent operates in isolated context:
1. **No cross-agent memory sharing**
2. **Foreman-only integration point**
3. **Sanitized input/output channels**
4. **Version-locked dependencies**

### Checkpointing
- Every review saved to `reviews/checkpoint/[timestamp]/`
- Rollback capability to any checkpoint
- Atomic commit on completion

---

## USAGE INSTRUCTIONS

### To Activate Standard Review (1–9):
```
AGENT: Foreman
MODE: 1235-standard
SUBJECT: [item to review]
OUTPUT: Single report
```

### To Activate Accelerated Review (10+):
```
AGENT: Foreman
MODE: 1235-accelerated
SUBJECT: [item to review]
TEAM: Spawn TEAM ALPHA — I
OUTPUT: Consolidated report
```

### To Activate Maximum Capacity (31+):
```
AGENT: Foreman
MODE: 1235-maximum
SUBJECT: [item to review]
TEAMS: Spawn multiple teams
SCALING: Additive +90
OUTPUT: Master consolidated report
```

---

## AGENT EQUIP CHECKLIST

Before sub-agent deployment, verify:
- [ ] AGENTS.md updated with team roles
- [ ] Framework protocols file accessible
- [ ] Satire-Skills-Bible indexed
- [ ] Token optimization settings configured
- [ ] Context drift protection active
- [ ] Checkpoint directory writable
- [ ] Master Plan compliance badge present

---

Framework Version: 1.0.0
Activation Date: 2026-04-01
Status: APPROVED — READY FOR DEPLOYMENT
