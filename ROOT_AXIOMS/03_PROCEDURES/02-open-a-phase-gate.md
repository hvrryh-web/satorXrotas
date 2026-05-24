[Ver001.000]

# PROC-02 — Open a Phase Gate

1. Locate the gate in `.agents/PHASE_GATES.md`. Confirm every unlock criterion is satisfied (link evidence — PR numbers, dashboard URLs, ADR IDs).
2. Get explicit sign-off from at least one CODEOWNER. Comment thread on the gate-opening PR is the record.
3. Edit `.agents/PHASE_GATES.md`: flip `LOCKED` → `OPEN`. Add an `Opened: YYYY-MM-DD` cell.
4. Append a row to `.agents/DECISION_LOG.md`:
   ```
   YYYY-MM-DD | <agent> | phase | Opened gate G<N>.<name>; evidence: …
   ```
5. If the gate opening implies new architecture (engine choice, persistence model), the same PR must include an ADR.
6. Open `.agents/phase-logbooks/PHASE-<N>-LOGBOOK.md` and add an entry describing what just unlocked.
7. PR title: `[framework] open gate G<N>.<name>`.
