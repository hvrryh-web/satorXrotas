[Ver001.000]

# Verification Matrix Protocol — NJZ RAT-OS

> **Purpose:** every "DONE" claim across the project must be backed by
> evidence that an auditor (human or agent) can mechanically check.
> This document specifies the schema, the per-session production
> rhythm, and the surfacing of unverified claims.
> **Status:** active.
> **Authored:** 2026-05-30.

---

## 1. Why this exists

Across the 13-PR session arc that closed Phase 0 / opened Phase 1, the
DECISION_LOG records 30+ task closures. Without a mechanical evidence
trail, a fresh agent re-asks "did this really land?" for every row —
burning context-budget on re-verification rather than new work.

The verification matrix gives every closed task a single row of:

```
ID  ·  TITLE  ·  STATUS  ·  PR  ·  SHA  ·  TESTS  ·  ARTEFACTS  ·  RUNBOOKS  ·  TELEMETRY-EVENTS
```

A fresh agent reads the matrix instead of the DECISION_LOG narrative.

---

## 2. Schema (per row)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | ✓ | Per `TASK_FORMAT_CONVENTION.md` §1 |
| `title` | string | ✓ | ≤ 80 chars |
| `status` | enum | ✓ | Per convention §2 |
| `pr` | integer | when `SHIPPED` | GitHub PR # |
| `sha` | string (7+ chars) | when `SHIPPED` | squash-merge commit on `main` |
| `testFiles` | array of paths | when tests added | repo-relative |
| `testCount` | integer ≥ 0 | when tests added | passing tests only |
| `artefacts` | array | optional | code files / dirs touched |
| `runbooks` | array | optional | `docs/operations/RUNBOOKS/*.md` |
| `telemetryEvents` | array | optional | `NjzEventMap` keys touched |
| `gateAffected` | string | optional | `G1.focus-hero`, etc. |
| `dependencies` | array of IDs | optional | prerequisite tasks |
| `notes` | string | optional | one paragraph max |

---

## 3. Per-session rhythm

1. **Session start.** A fresh agent reads the latest matrix at
   `docs/program-management/VERIFICATION_MATRIX.md` (when produced) +
   `.agents/handoff/session-*.md`. The matrix is the source of truth
   for "what's actually shipped".

2. **During the session.** As each PR lands on `main`, append rows to
   the matrix in the same commit as the DECISION_LOG entry.

3. **Session close.** A close handoff cites the matrix delta (rows
   added + status transitions) rather than re-narrating the work.

4. **Verification audit.** Once per session, run the audit:
   - Every `SHIPPED` row's `pr` + `sha` exists on `main`.
   - Every `testFiles` path exists and passes locally.
   - Every `runbooks` path exists.
   - Every `telemetryEvents` key exists in `NjzEventMap`.
   - Surface any mismatch as a `BLOCKED` audit follow-up.

---

## 4. Matrix file location & format

**Canonical path:** `docs/program-management/VERIFICATION_MATRIX.md`.

**Format:** Markdown table, one row per task. Newest at the bottom
(append-only chronological). When the file grows beyond ~500 rows,
split into per-year files (`VERIFICATION_MATRIX-2026.md`) and keep a
rolling index.

**Template row** (column header line + one example):

```markdown
| id | title | status | pr | sha | testFiles | testCount | runbooks | telemetryEvents | gateAffected | dependencies |
|----|-------|--------|----|-----|-----------|-----------|----------|-----------------|--------------|--------------|
| A-1-04 | useFocusSession hook | SHIPPED | 32 | ed8186c | packages/@njz-os/focus-engine/src/machine.test.ts | 17 | — | progression.event | G1.focus-hero (LOCKED) | A-1-01, A-1-02 |
```

---

## 5. Generation (tool path)

A future tool `tools/verification-matrix/index.mjs` (queued for INFRA
follow-up) reads:

- `git log --merges` for the PR list since the prior matrix.
- The corresponding commit's diff for `testFiles` + `runbooks`.
- The DECISION_LOG entries timestamped on the same date for `id` +
  `title` mapping.
- The EXPANDED.md task list for `dependencies`.

…and emits the matrix rows. Until that tool ships, rows are appended
by hand in the same PR that ships the work.

---

## 6. Surfacing unverified claims

When a row exists in the DECISION_LOG **but not** in the matrix, an
agent treats the work as unverified for planning purposes — i.e.,
treats it like a `SCAFFOLDED` row needing follow-up.

When the matrix row's PR / SHA is missing or stale, the row is
`BLOCKED-UNVERIFIED` until the audit closes the gap.

This pulls the cost of "did this really land?" out of every future
session and concentrates it in the audit pass.

---

## 7. Backfill plan (this session's session arc)

PRs #25 .. #37 will be back-filled into the matrix once the matrix
file lands (separate commit in the governance refresh PR). Until then
the DECISION_LOG + per-PR titles serve as the evidence map.

---

## 8. Cross-references

- `docs/governance/TASK_FORMAT_CONVENTION.md` — defines the ID + status enum + evidence sub-record.
- `docs/governance/LANE_CLOSURE_MANIFEST_TEMPLATE.md` — per-lane closure checklist that feeds rows here.
- `.agents/DECISION_LOG.md` — narrative log; matrix is the structured projection.
- `.agents/PHASE_GATES.md` — gate column references rows here.

---

*Living document. Updates require an ADR or DECISION_LOG entry.*
