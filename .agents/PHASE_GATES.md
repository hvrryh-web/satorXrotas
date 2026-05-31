[Ver001.000]

# PHASE_GATES — NJZ RAT-OS

Phase gates encode "what's unlocked right now". An agent must not implement features behind a locked gate without an explicit user override. CI enforces gates where possible.

## Current Phase

**Phase 1 — Implementation** (active as of 2026-05-30).

Phase 0 (Foundation) closed implicitly when the first Phase-1 lane code
landed on `main` (PR #30, Lane E auth shell). The Phase-0 exit criteria
below are retroactively considered met; phase logbook entry forthcoming.

## Gate Status

| Gate | Phase | Status | Unlock criteria | Status notes (2026-05-30) |
|------|-------|--------|-----------------|---------------------------|
| `G0.framework` | 0 | **OPEN** | Always — bootstrap gate | |
| `G0.docs` | 0 | **OPEN** | Always — product + architecture docs editable | |
| `G0.skeleton` | 0 | **OPEN** | Always — monorepo + app + package skeletons editable | |
| `G0.adapters` | 0 | **OPEN** | Always — type stubs allowed | |
| `G1.focus-hero` | 1 | LOCKED · unlock-pending | ADR-0009 Accepted + Lane A tasks A1-A8 closed | A1/A2/A4/A5/A6 SHIPPED (PR #32). Remaining: A3, A7, A8. Risk row R-001. |
| `G1.soundscapes` | 1 | LOCKED · unlock-pending | ADR-0010 Accepted + Lane B tasks B1-B8 closed | B1/B2/B3/B4/B7 SHIPPED (PR #34). Remaining: B5, B6, B8. Risk rows R-003..R-005. |
| `G1.blocker` | 1 | LOCKED · unlock-pending | ADR-0011 Accepted + Lane D tasks D1-D7 closed | D1/D3/D6 SHIPPED (PR #36). Remaining: D2, D4, D5, D7. Risk rows R-008..R-011. |
| `G1.polyworld-office` | 1 | LOCKED · unlock-pending | ADR-0005 + ADR-0012 Accepted + Lane C tasks C1-C7 closed + asset pipeline live | C3/C4/C5/C6/C7 SHIPPED (PR #35). Remaining: C1, C2. Risk rows R-006, R-007. |
| `G1.webapp-auth` | 1 | LOCKED · unlock-pending | Lane E tasks E1-E8 closed + real Supabase wiring | E1/E2/E3/E5/E6/E7 SHIPPED (PRs #30, #31). Remaining: E4, E8. Risk rows R-012..R-014. |
| `G1.vaultbrain-live` | 1 | LOCKED | Vaultbrain extension shipped upstream + adapters integration-tested | Upstream issue #118 open (R-023); EPIC-01 surface ships against mock. |
| `G2.brain-training` | 2 | LOCKED | Phase 1 exit + ADR-0018 + ADR-0019 Accepted | |
| `G2.writing-space` | 2 | LOCKED | Phase 1 exit + ADR-0015 Accepted (editor stack) | SPRINT-01 bench scaffolded (R-017) |
| `G2.micro-learning` | 2 | LOCKED | Phase 1 exit + ADR-0016 + ADR-0017 Accepted | SPRINT-02 bench scaffolded (R-018) |
| `G2.polyworld-home` | 2 | LOCKED | Phase 1 exit + decoration system designed | |
| `G2.mobile-pwa` | 2 | LOCKED | Phase 1 exit | |
| `G2.premium` | 2 | LOCKED | Phase 1 exit + billing adapter integrated | |
| `G3.social` | 3 | LOCKED | Phase 2 exit | |
| `G3.native` | 3 | LOCKED | Phase 2 exit | |
| `G3.events` | 3 | LOCKED | Phase 2 exit | |

### `unlock-pending` status

`LOCKED · unlock-pending` means: ADR prerequisites + part of the lane
work have landed but the gate has NOT been flipped because at least
one task in the lane's closure manifest is still TODO / IN_PROGRESS /
SCAFFOLDED. CODEOWNER opens the gate by:

1. Verifying the lane closure manifest shows all `SHIPPED` rows.
2. Confirming the lane's E2E suite is green.
3. Confirming the performance budget for the lane is honoured per `docs/governance/PERFORMANCE_DEFINITIONS.md` §4.
4. Flipping the row from `unlock-pending` → `OPEN`.
5. Logging the flip in DECISION_LOG + a logbook entry.

## How Gates Are Enforced

- **Editorial:** CODEOWNER review must confirm gate is open before approving a PR that adds feature code behind a locked gate.
- **Build:** `apps/web/src/modules/<module>/index.ts` will export from `__phase__.ts` which throws at module-load time if the gate is locked. This forces accidental feature work to fail fast.
- **CI:** `tools/doc-tier-check/index.mjs --gates` validates that no file under `apps/web/src/modules/<module>/` exists when the corresponding gate is locked.

## Opening a Gate

1. Verify all unlock criteria in the table above.
2. Get sign-off from one CODEOWNER (see `CODEOWNER_CHECKLIST.md`).
3. Update this table — flip `LOCKED` to `OPEN` with the date.
4. Append a row to `.agents/DECISION_LOG.md`.
5. Add an ADR if the gate opening involves an architecture choice not previously decided.

## Phase 0 Exit Criteria (from MASTER_PLAN.md)

- [ ] All Phase 0 workstreams merged on `main`.
- [ ] `pnpm install && pnpm build` succeeds with placeholder content.
- [ ] `pnpm typecheck` passes with zero errors.
- [ ] `.doc-tiers.json` validation passes; no orphan root `.md` files.
- [ ] ADR-0001 through ADR-0008 all `Status: Accepted` (0003 superseded by 0008; 0002 partially superseded by 0007).
- [ ] DR-0001 (bootstrap dev report) merged.
- [ ] One end-to-end smoke route in `apps/web` renders without errors.
