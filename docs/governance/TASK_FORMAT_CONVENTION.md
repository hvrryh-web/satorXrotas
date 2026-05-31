[Ver001.000]

# Task Format Convention — NJZ RAT-OS

> **Purpose:** every task, work item, refinement, or follow-up across
> the project shares one structured shape so AI agents and humans parse
> them the same way, evidence flows mechanically, and the verification
> matrix can be generated automatically.
> **Status:** active · supersedes ad-hoc to-do bullets in `.agents/handoff/*`.
> **Authored:** 2026-05-30 (post Phase-1 lane sweep).

---

## 1. Canonical ID

```
<LANE>-<PHASE>-<NN>[.<SUB>]
```

| Component | Allowed values | Example |
|-----------|----------------|---------|
| `LANE`    | `A` `B` `C` `D` `E` `F` `W` `L` `B'` `PRX-25` `OPS` `INFRA` `GOV` | `A`, `PRX-25` |
| `PHASE`   | `0` `1` `2` `3` (project phase) | `1` |
| `NN`      | zero-padded two-digit task counter inside the lane × phase | `04` |
| `.SUB`    | optional dotted sub-task counter (one level only) | `.2` |

Examples:

- `A-1-04` — Lane A, Phase 1, task 4 (`useFocusSession` React hook).
- `A-1-04.2` — sub-task: cross-tab `useSyncExternalStore` integration.
- `PRX-25-EPIC-01` — PR-25 portfolio uplift, epic 1 (`vaultbrain-client`).
- `INFRA-1-02` — infra phase-1 task 2 (Lighthouse CI).

Existing IDs in `docs/program-management/PR-25-portfolio-uplift.md` and
the EXPANDED.md docs are grandfathered and need not be renumbered.

---

## 2. Status enum

| Status | Meaning |
|--------|---------|
| `TODO` | Defined, not started |
| `IN_PROGRESS` | Branch open, work underway |
| `BLOCKED` | Cannot proceed without an external input (decision / credential / ADR) |
| `DEFERRED` | Intentionally postponed; carries a follow-up trigger condition |
| `SCAFFOLDED` | Surface + harness + tests exist; the load-bearing run is queued |
| `SHIPPED` | Merged to `main` with evidence; closes the task |
| `WITHDRAWN` | Decided not to do; reason captured in DECISION_LOG |

`TODO → IN_PROGRESS → SHIPPED` is the happy path. Other transitions are
explicit (no silent retreat).

---

## 3. Acceptance Evidence Schema

Every task carries an `evidence` block once it leaves `TODO`. Stored
inline in the lane closure manifest:

```yaml
evidence:
  pr: 32                                      # GitHub PR number
  sha: ed8186c                                # squash commit on main
  testFiles:                                  # vitest / playwright / shell-test
    - packages/@njz-os/focus-engine/src/machine.test.ts
  testCount: 17                               # passing tests added
  runbooks: []                                # docs/operations/RUNBOOKS/*.md
  telemetryEvents: []                         # NjzEventMap keys emitted
  threatModelDelta: null                      # path/URL to delta or null
  budgetImpact:
    bundleKbGz: 0                             # delta vs main
    fcpMs: 0
```

A `SCAFFOLDED` status MUST list the harness location + the missing
load-bearing input that gates the final run.

A `SHIPPED` status MUST list `pr` + `sha` + `testFiles` (testCount > 0
unless task is doc-only).

---

## 4. Per-Task Required Fields

Tasks live inside an EXPANDED.md task list, the PR-25 uplift doc, or a
lane closure manifest. They MUST include:

| Field | Notes |
|-------|-------|
| `id` | Per §1 |
| `title` | ≤ 80 chars |
| `status` | Per §2 |
| `ownerRole` | One of: Implementer · Architect · Designer · Critic · Coordinator · Data Engineer · Security |
| `reviewerRole` | Different from owner; defaults to Architect on `feat:`, Critic on `fix:`, Coordinator on `docs:` |
| `surface` | Workspace paths the task is allowed to touch |
| `acceptanceCriteria` | Bulleted, each independently checkable |
| `dependencies` | IDs of prerequisite tasks; `null` when none |
| `evidence` | Per §3; required for non-TODO status |
| `effortEstimate` | Ideal-engineer-days; integer ≥ 1 |
| `iceScore` | Impact × Confidence × Ease (1-10 each); optional but recommended |
| `telemetryImpact` | Which NjzEventMap keys change; `null` when none |
| `outOfScope` | Bulleted list — what this task explicitly does NOT cover |

---

## 5. Task list rendering

Task lists in PR bodies / handoffs render as Markdown tables. The
columns above map 1:1 to columns. Use checklist boxes only for the
status field's collapsed view.

```markdown
| ID | Title | Status | Owner | Evidence |
|----|-------|--------|-------|----------|
| A-1-04 | useFocusSession hook | SHIPPED | Implementer | PR #32 @ ed8186c |
| A-1-04.2 | useSyncExternalStore | DEFERRED | Implementer | — |
```

For finer detail, link the row to the full task record in the EXPANDED.md
or the lane closure manifest.

---

## 6. Subtask convention

A subtask is justified when:

- The parent task spans more than 1 commit cleanly, AND
- The subtask is independently verifiable, AND
- The subtask has its own acceptance criteria.

Do NOT create subtasks for incidental refactors discovered along the
way — those land in the parent task's commit.

---

## 7. Closing a task

Close conditions:

1. Status transitions `IN_PROGRESS → SHIPPED` only when the PR's
   evidence block matches the task's acceptance criteria 1:1.
2. The Lane Closure Manifest row updates to reflect new status.
3. DECISION_LOG.md appends one line per closed task in the format:

   ```
   YYYY-MM-DD | <agent> | <area> | <one-sentence decision> [→ <task-id>]
   ```

4. Any related `OUT_OF_SCOPE_FOLLOW_UPS` rows in the manifest get
   created or refreshed.

---

## 8. Cross-references

- `docs/governance/PERFORMANCE_DEFINITIONS.md` — what counts as "fast enough" per lane.
- `docs/governance/VERIFICATION_MATRIX_PROTOCOL.md` — how evidence flows into the matrix.
- `docs/governance/LANE_CLOSURE_MANIFEST_TEMPLATE.md` — template that consumes this convention.
- `.agents/AGENT_CONTRACT.md` — behavioural contract referencing this convention.
- `.agents/RISK_REGISTER.md` — deferred / out-of-scope items live there.

---

*Living document. Updates require an ADR or a DECISION_LOG entry.*
