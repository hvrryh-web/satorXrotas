[Ver001.000]

# Monthly Cleanup Protocol — NJZ RAT-OS

Once per month, the Coordinator agent runs this protocol. Output: one cleanup PR + an updated `.agents/PROJECT_STATUS_OVERVIEW.md`.

## Cadence

First Friday of each month.

## Checklist

### 1. Tier audit (`.doc-tiers.json`)

- [ ] All `T0` files exist.
- [ ] All `T1` paths resolve (file or dir).
- [ ] `manifest.approved_root_files` matches actual root-level `.md` files.
- [ ] Any `xCOMP_*` files truly live in `archive/`.

### 2. ADR audit

- [ ] All ADRs have a status (no missing field).
- [ ] No ADRs in `Proposed` for more than 30 days — either accept, reject, or document why.
- [ ] Cross-references from `DECISION_LOG.md` resolve.

### 3. Phase gate audit

- [ ] `PHASE_GATES.md` reflects ground truth. Any feature code without its gate OPEN is drift — log to `drift-yyyy-mm.md`.

### 4. Schema registry audit

- [ ] All types listed in `SCHEMA_REGISTRY.md` still exist in code.
- [ ] All exported types in `@njz-os/core/src/*` are listed (or explicitly excluded).

### 5. Doc registry audit

- [ ] Every route in `.doc-registry.json` resolves.
- [ ] No "404 query" common in recent agent sessions — if there is, add a route.

### 6. Upstream alignment

- [ ] Compare RAT-OS `.agents/` and `ROOT_AXIOMS/` to upstream `notbleaux/ZeSporteXte` equivalents. Surface meaningful divergence.
- [ ] Check `@njz/*` package versions in `package.json` vs latest published — flag bumps available.

### 7. Stale files

- [ ] Any `.agents/active/` file with no commit reference in 30 days → move to `handoff/` or close.
- [ ] Any `.agents/session/` file older than the current sprint → delete.
- [ ] Any `docs/dev-reports/` Draft older than 14 days → finalize or delete.

### 8. CI health

- [ ] CI median runtime over the last month.
- [ ] Flaky test count.
- [ ] Coverage delta.

### 9. Channel hygiene

- [ ] Any PR open >7 days needs an owner-tag refresh.

## Output

- PR titled `[framework] monthly cleanup YYYY-MM`.
- Update `.agents/PROJECT_STATUS_OVERVIEW.md` with the snapshot.
- Append a row to `.agents/DECISION_LOG.md` if anything substantive surfaced.
- Open follow-up issues for any drift category > Low.
