# Satire-Skills-Bible
## Agent Skill Registry for Satire-deck-Veritas

---

## PURPOSE

This bible catalogs all skills, tools, and capabilities available to agents working on Satire-deck-Veritas. It serves as:
- Quick reference for what agents can do
- Index of available tools and frameworks
- Skill creation template
- Capability advertisement to users

---

## SKILL CATEGORIES

### 🔧 CORE SKILLS

| Skill | Description | Status |
|-------|-------------|--------|
| file-ops | Read, write, edit files | ✅ Active |
| shell-exec | Execute shell commands | ✅ Active |
| web-search | Search internet for information | ✅ Active |
| web-fetch | Fetch and parse web content | ✅ Active |
| browser-control | Automate browser actions | ✅ Active |
| git-ops | Git commit, push, branch | ✅ Active |
| session-spawn | Spawn sub-agents | ✅ Active |

### 🎨 DESIGN SKILLS

| Skill | Description | Status |
|-------|-------------|--------|
| wireframe-create | Generate HTML wireframes | ✅ Active |
| design-token-validate | Check design system compliance | ✅ Active |
| screenshot-capture | Capture browser screenshots | ✅ Active |
| color-analysis | Extract and analyze color palettes | ✅ Active |
| typography-scale | Generate type scales | ⏳ Planned |

### 🏗️ DEVELOPMENT SKILLS

| Skill | Description | Status |
|-------|-------------|--------|
| component-create | Build React/Vue components | ✅ Active |
| css-generate | Write production CSS | ✅ Active |
| api-design | Design REST/GraphQL APIs | ✅ Active |
| database-schema | Create SQL schemas | ✅ Active |
| validation-script | Write check scripts | ✅ Active |

### 📊 ANALYSIS SKILLS

| Skill | Description | Status |
|-------|-------------|--------|
| code-review | Review code for quality | ✅ Active |
| design-critique | Critique visual designs | ✅ Active |
| ppt-extract | Extract content from PPT files | ✅ Active |
| docx-extract | Extract content from DOCX files | ✅ Active |
| data-analysis | Analyze datasets | ⏳ Planned |

### 🤖 AGENT COORDINATION SKILLS

| Skill | Description | Status |
|-------|-------------|--------|
| 1235-review | Execute 1235 framework reviews | ✅ Active |
| sub-agent-spawn | Spawn and manage sub-agents | ✅ Active |
| context-inject | Inject context to agents | ✅ Active |
| token-optimize | Optimize token usage | ✅ Active |
| color-protocol | Use color-coded communication | ✅ Active |

---

## SKILL DEFINITIONS

### SKILL: 1235-review
**Full Name:** 1235 do((do)*) Review Framework  
**Category:** Agent Coordination  
**Status:** ✅ Active  
**File:** `docs/frameworks/1235-REVIEW/1235-do-framework.md`

**Description:**
Comprehensive review protocol producing:
- 1 Review Report
- 2 Success Deliverables
- 3 Recommendations (with 5 sub-bullets each)
- Recursive sub-agent activation for reviews 10+

**Activation:**
```
MODE: 1235-[standard|accelerated|maximum]
SUBJECT: [item to review]
TEAM: [if accelerated+]
```

**Output:**
- Structured markdown report
- Validation matrix
- Actionable recommendations

---

### SKILL: wireframe-create
**Full Name:** Wireframe Generation  
**Category:** Design  
**Status:** ✅ Active  
**File:** `tools/prompts/01-wireframe-generation.md`

**Description:**
Creates HTML wireframes following strict design system:
- 0px border radius (sharp corners)
- [#TEA] teal for data
- [#ORG] orange for CTAs
- Zero-scroll layouts
- Quadrant modularity

**Input Requirements:**
- Visual specification document
- Color protocol
- Component inventory

**Output:**
- Single HTML file with inline CSS
- Validation checklist
- Screenshot for review

---

### SKILL: file-access-protocol
**Full Name:** Accessible File Delivery  
**Category:** Core  
**Status:** ✅ Active  
**File:** `docs/frameworks/AGENT-COORDINATION/file-access-protocol.md`

**Description:**
Ensures all files are delivered in accessible formats:
- Direct content paste (text)
- Browser screenshots (visual)
- GitHub links (repositories)
- Summarized reports (bulk)

**Methods:**
1. Direct Content Paste — for markdown, code
2. Browser Screenshots — for HTML, UI
3. GitHub Repository — for large projects
4. Summarized Reports — for multiple files

---

## SKILL CREATION TEMPLATE

To add a new skill:

```markdown
### SKILL: [skill-id]
**Full Name:** [Human-readable name]
**Category:** [Category]
**Status:** [✅ Active | ⏳ Planned | 🚧 WIP]
**File:** [path to documentation]

**Description:**
[What it does]

**Prerequisites:**
- [List dependencies]

**Input:**
- [Required inputs]

**Output:**
- [Expected outputs]

**Example Usage:**
```
[Example command or prompt]
```

**Notes:**
[Additional information]
```

---

## AGENT-SPECIFIC SKILLS

### Foreman (You)
- All core skills
- All coordination skills
- Sub-agent orchestration
- Final approval authority

### Generalis (Generalist Sub-Agent)
- file-ops
- web-search
- web-fetch
- 1235-review (standard mode)
- context-inject

### Interface (Front-End Specialist)
- wireframe-create
- component-create
- css-generate
- design-token-validate
- screenshot-capture

### Structura (Back-End Specialist)
- api-design
- database-schema
- validation-script
- git-ops
- session-spawn

---

## SKILL STATUS LEGEND

| Symbol | Status | Meaning |
|--------|--------|---------|
| ✅ | Active | Ready for use |
| ⏳ | Planned | Defined, not implemented |
| 🚧 | WIP | In development |
| 🧪 | Experimental | Testing phase |
| ❌ | Deprecated | Do not use |

---

## QUICK REFERENCE

**Most Used Skills:**
1. file-ops — Every session
2. wireframe-create — Design tasks
3. 1235-review — Quality assurance
4. file-access-protocol — All deliveries
5. git-ops — Repository management

**New Skills Needed:**
- automated-testing
- performance-profiling
- security-audit
- accessibility-check
- cross-browser-validation

---

Bible Version: 1.0.0
Last Updated: 2026-04-01
Status: 7 Active, 2 Planned
