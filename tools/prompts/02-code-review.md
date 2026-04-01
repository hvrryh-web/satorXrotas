# Optimized Prompt: Code Review & CRIT
## For Established Chats (1 Token Per Response)

---

## PROMPT (COPY & PASTE)

```
AGENT: CRITIC [#RED]
TASK: Review TENET Portal v3

DELIVERABLE: [paste HTML/CSS]
SPEC SOURCE: visual-spec-v3.md

VALIDATION MATRIX:
┌─────────────────┬──────────┬──────────┬────────┐
│ Check           │ Expected │ Actual   │ ✓/✗    │
├─────────────────┼──────────┼──────────┼────────┤
│ Background      │ #0A0A0A  │ [auto]   │ [ ]    │
│ Border-radius   │ 0px      │ [auto]   │ [ ]    │
│ HUB tile count  │ 4        │ [auto]   │ [ ]    │
│ Feature cards   │ 0        │ [auto]   │ [ ]    │
│ Teal usage      │ data     │ [auto]   │ [ ]    │
│ Orange usage    │ CTAs     │ [auto]   │ [ ]    │
│ Vignette masks  │ yes      │ [auto]   │ [ ]    │
│ Scroll required │ no       │ [auto]   │ [ ]    │
└─────────────────┴──────────┴──────────┴────────┘

SCORING:
- Spec adherence: __/10
- Visual quality: __/10
- Code quality: __/10
- Constraint compliance: __/10
TOTAL: __/10

DECISION: [APPROVE / REVISE / REJECT]

IF REVISE/REJECT:
VIOLATIONS:
1. [Line X]: [Issue] → [Fix]
2. [Line Y]: [Issue] → [Fix]
3. ...

EXECUTE NOW. RETURN MATRIX ONLY.
```

---

## DELIVERABLE FORMAT

Agent responds with:

```
VALIDATION MATRIX:
┌─────────────────┬──────────┬──────────┬────────┐
│ Check           │ Expected │ Actual   │ ✓/✗    │
├─────────────────┼──────────┼──────────┼────────┤
│ Background      │ #0A0A0A  │ #0A0A0A  │ ✓      │
│ Border-radius   │ 0px      │ 16px     │ ✗      │
│ HUB tile count  │ 4        │ 4        │ ✓      │
│ Feature cards   │ 0        │ 8        │ ✗      │
│ Teal usage      │ data     │ data     │ ✓      │
│ Orange usage    │ CTAs     │ stats    │ ✗      │
│ Vignette masks  │ yes      │ yes      │ ✓      │
│ Scroll required │ no       │ yes      │ ✗      │
└─────────────────┴──────────┴──────────┴────────┘

SCORES:
- Spec adherence: 4/10
- Visual quality: 6/10
- Code quality: 8/10
- Constraint compliance: 3/10
TOTAL: 5.25/10

DECISION: REJECT

VIOLATIONS:
1. Line 23: border-radius: 16px → change to 0px
2. Lines 45-89: 8 feature cards → remove all
3. Line 67: color: #F97316 on stats → change to #14B8A6
4. Line 112: overflow-y: scroll → remove, fit to 100vh

RETURN TO: IMPLEMENTER
```

---

## DECISION THRESHOLDS

| Score | Decision | Action |
|-------|----------|--------|
| ≥ 9.0 | APPROVE | Forward to COORDINATOR |
| 7.0-8.9 | REVISE | Return to IMPLEMENTER |
| < 7.0 | REJECT | Return to IMPLEMENTER |

---

## COMMUNICATION PROTOCOL

| You Say | Agent Does |
|---------|------------|
| "CRIT" | Runs validation matrix |
| "DETAIL" | Expands specific violation |
| "COMPARE" | Side-by-side spec vs actual |
| "APPROVE" | Confirms and forwards |
| "REJECT" | Lists all violations |

---

## TOKEN OPTIMIZATION

Each response:
- Matrix format only
- No prose
- Exact line numbers
- Precise fix instructions
- Under 500 tokens

---

Prompt Version: 3.0.0
Optimization: 1-token responses
Last Updated: 2026-03-31
