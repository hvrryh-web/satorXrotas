[Ver001.000]

# PHASE_GATES — NJZ RAT-OS

Phase gates encode "what's unlocked right now". An agent must not implement features behind a locked gate without an explicit user override. CI enforces gates where possible.

## Current Phase

**Phase 0 — Foundation** (active).

## Gate Status

| Gate | Phase | Status | Unlock criteria |
|------|-------|--------|-----------------|
| `G0.framework` | 0 | **OPEN** | Always — this is the bootstrap gate |
| `G0.docs` | 0 | **OPEN** | Always — product + architecture docs editable in Phase 0 |
| `G0.skeleton` | 0 | **OPEN** | Always — monorepo + app + package skeletons editable |
| `G0.adapters` | 0 | **OPEN** | Always — type stubs allowed; no live calls yet |
| `G1.focus-hero` | 1 | LOCKED | Phase 0 exit + ADR-0007 (focus engine design) accepted |
| `G1.soundscapes` | 1 | LOCKED | Phase 0 exit + ADR-0008 (audio engine choice) accepted |
| `G1.blocker` | 1 | LOCKED | Phase 0 exit + ADR-0009 (blocker enforcement model) accepted |
| `G1.polyworld-office` | 1 | LOCKED | Phase 0 exit + ADR-0010 (polyworld renderer) accepted + asset pipeline live |
| `G1.vaultbrain-live` | 1 | LOCKED | Adapters integration-tested against upstream staging |
| `G2.brain-training` | 2 | LOCKED | Phase 1 exit criteria (5,000 MAU, D7 ≥ 18%) |
| `G2.writing-space` | 2 | LOCKED | Phase 1 exit + ADR-0011 (editor stack) accepted |
| `G2.micro-learning` | 2 | LOCKED | Phase 1 exit + content pipeline defined |
| `G2.polyworld-home` | 2 | LOCKED | Phase 1 exit + decoration system designed |
| `G2.mobile-pwa` | 2 | LOCKED | Phase 1 exit |
| `G2.premium` | 2 | LOCKED | Phase 1 exit + billing adapter integrated |
| `G3.social` | 3 | LOCKED | Phase 2 exit |
| `G3.native` | 3 | LOCKED | Phase 2 exit |
| `G3.events` | 3 | LOCKED | Phase 2 exit |

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
- [ ] ADR-0001 through ADR-0006 all `Status: Accepted`.
- [ ] DR-0001 (bootstrap dev report) merged.
- [ ] One end-to-end smoke route in `apps/web` renders without errors.
