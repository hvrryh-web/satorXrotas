[Ver001.000]

# Contracts Drift Runbook

How RAT-OS detects, reports, and reconciles drift between its **vendored**
upstream contracts and the upstream source of truth.

## When to use

- An automated drift issue lands on `hvrryh-web/satorXrotas` from the
  weekly `Contracts drift` workflow.
- Manual: when you suspect upstream has changed an OpenAPI surface and
  want to check.
- Phase-4 gate prep: when `G4.ai-personalization` is being opened, the
  vendored `agent-gateway.yaml` must be fresh.

## Preconditions

- Logged into GitHub with read access to `notbleaux/ZeSporteXte`.
- `GITHUB_TOKEN` (or `GH_TOKEN`) in env if you're hitting rate limits.
- Node 20 + PyYAML installed: `pip install pyyaml`.

## Steps

1. **Run the refresh script.**

   ```bash
   pnpm contracts:refresh-agent-gateway
   ```

   - Exit 0 → no drift; the vendored file is current. Done.
   - Exit 1 → drift found; the file has been updated in your working tree
     with a new pinned SHA in the header.

2. **Inspect the diff.**

   ```bash
   git --no-pager diff -- contracts/openapi/agent-gateway.yaml | less
   ```

   Read the diff with the lens "does our adapter code need to change?".
   Look for:

   - **New endpoints** — opportunities, not breaks. Don't auto-consume.
   - **Renamed paths** — breaks the consumer-side spec if we already
     referenced the old path in `packages/adapters/agent-gateway-client/`.
   - **Removed endpoints** — track upstream deprecation notes.
   - **Schema changes on existing endpoints** — review the field-by-field
     diff against any `@njz-os/*` types that consume those shapes.

3. **Decide: accept, defer, or reject.**

   | Outcome | Action |
   |---------|--------|
   | Accept (upstream change is desirable, no consumer code changes) | Commit the updated YAML in a `chore(contracts): refresh agent-gateway pin` PR |
   | Accept with consumer changes | Branch + commit YAML + adapter updates + tests in one PR |
   | Defer | Close the drift issue with `not-planned` reason; the next weekly run will reopen it |
   | Reject (upstream change conflicts with RAT-OS direction) | Open a discussion thread on `notbleaux/ZeSporteXte`; do not bump the pin |

4. **Update `.agents/DECISION_LOG.md`** when you bump (or deliberately
   refuse to bump):

   ```
   YYYY-MM-DD | <agent> | contracts | agent-gateway pin <old-sha> → <new-sha> (or: refused — <reason>)
   ```

5. **Close the drift issue.** Reference the PR (or the DECISION_LOG entry
   if refused).

## Verification

- `pnpm contracts:refresh-agent-gateway` on the resulting branch exits 0
  (no further drift vs the pin).
- `pnpm typecheck` and `pnpm lint` remain green (no adapter regressions).
- The drift issue is closed with a link to the resolving PR or rationale.

## Rollback

If a drift-driven update breaks consumers:

```bash
git revert <commit-sha>
git push
```

The pin reverts to the prior upstream SHA. Drift issue re-opens on the
next weekly run; deal with it next iteration.

## Postconditions

- `contracts/openapi/agent-gateway.yaml` header carries the new pinned
  SHA + ISO date + agent that pinned it.
- Any consumer-side changes ship in the same PR as the pin bump.
- `.agents/DECISION_LOG.md` has a one-line entry for the bump.

## See also

- ADR-0014 (vendoring decision, Accepted).
- `tools/contracts/refresh-agent-gateway.mjs` — the script.
- `.github/workflows/contracts-drift.yml` — the weekly check.
- `.agents/active/upstream-coordination.md` — overall upstream coordination thread.
