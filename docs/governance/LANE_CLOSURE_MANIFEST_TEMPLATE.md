[Ver001.000]

# Lane Closure Manifest Template — NJZ RAT-OS

> **Purpose:** every lane (A, B, C, D, E in Phase 1; W, L, B′ in Phase
> 2; plus PR-25 horizontal items) closes with a single manifest
> document mapping every EXPANDED.md task to status + evidence + the
> PR-25 uplift items it consumes. Replaces ad-hoc "what shipped" prose
> with a structured shape an agent can scan in seconds.
> **Status:** active template.
> **Authored:** 2026-05-30.

---

## 1. File location

`docs/program-management/LANE_<LETTER>_MANIFEST.md`

Examples:
- `LANE_A_MANIFEST.md` — Focus Engine + Hero UI
- `LANE_PRX_25_MANIFEST.md` — portfolio uplift items (alternative
  format to PR-25 doc §G.1)

One manifest per lane, updated in the same PR that ships new lane
work. The manifest is the source of truth for "what's the lane's exact
state right now".

---

## 2. Template

Copy below into the lane's manifest file at first use; replace
`{{placeholders}}`.

```markdown
[Ver001.000]

# Lane {{X}} — Closure Manifest

> **Module:** {{module name}}
> **Spec:** docs/modules/{{slug}}/EXPANDED.md
> **Gate protected:** {{G1.xxx}}
> **Source ADRs:** {{ADR-NNNN, ADR-NNNN}}
> **Phase:** {{1 | 2}}
> **Last refresh:** {{YYYY-MM-DD}}

## Tasks (from EXPANDED.md §4)

| ID | Title | Status | PR | SHA | Tests | Notes |
|----|-------|--------|----|-----|-------|-------|
| {{X}}-{{N}}-01 | {{task title}} | TODO / IN_PROGRESS / SCAFFOLDED / SHIPPED / DEFERRED / BLOCKED / WITHDRAWN | #NN | abcdef1 | N/N | one-liner |

## PR-25 uplift items consumed by this lane

| Item | Status when this lane closes |
|------|------------------------------|
| PRX-25-EPIC-01 (vaultbrain-client) | SHIPPED (PR #27) |

## Cross-lane integrations

| Direction | Surface | Counterparty |
|-----------|---------|--------------|
| EMITS | {{progression.event}} | Lane C (decoration unlocks), PR-25 PATCH-04 (analytics) |
| CONSUMES | {{useAuth from Lane E}} | Lane E |

## Out-of-scope follow-ups

Each carries a row in `.agents/RISK_REGISTER.md` and is flagged for a
follow-up PR.

- `{{TASK_ID}}` — {{one-liner}}; **trigger** = {{what unblocks it}}.

## Gate flip criteria

Per `.agents/PHASE_GATES.md`, this gate flips OPEN when:

- [ ] All `SHIPPED` rows above are present on `main`.
- [ ] {{E2E suite name}} green.
- [ ] {{Performance budget name}} ≥ threshold per `docs/governance/PERFORMANCE_DEFINITIONS.md` §4.
- [ ] CODEOWNER sign-off on this manifest.
- [ ] Lighthouse perf ≥ 85 on the lane's primary route.

## Sign-off

- [ ] Implementer: __________ (date)
- [ ] Reviewer: __________ (date)
- [ ] Coordinator: __________ (date)

## Notes

{{Free-form section for cross-cutting notes. Keep brief.}}
```

---

## 3. Refresh cadence

| Trigger | Refresh |
|---------|---------|
| PR merged that touches this lane | Update the affected task rows + dates |
| Cross-lane event (EMITS / CONSUMES) introduced or retired | Update the integrations section |
| `OUT_OF_SCOPE_FOLLOW_UPS` row resolved | Move to the appropriate task row; remove from out-of-scope list |
| Gate flips | Coordinator updates Gate flip criteria + flips `.agents/PHASE_GATES.md` row in the same PR |

---

## 4. Cross-references

- `docs/governance/TASK_FORMAT_CONVENTION.md` — task ID + status enum + evidence shape used here.
- `docs/governance/VERIFICATION_MATRIX_PROTOCOL.md` — global matrix that this manifest's `SHIPPED` rows feed.
- `docs/governance/PERFORMANCE_DEFINITIONS.md` — performance thresholds referenced in gate criteria.
- `.agents/PHASE_GATES.md` — single source of truth for gate state.
- `.agents/RISK_REGISTER.md` — out-of-scope items carry rows here.

---

*Living template. Updates require a DECISION_LOG entry.*
