[Ver001.000]

# PROC-04 — Archive a Document

When a doc is no longer current — superseded by a new one, completed and not historically useful, or simply stale — archive it. Don't delete.

1. Move the file to `archive/<area>/<year>/<original-name>.md`.
2. Rename to add `xCOMP_` prefix: `xCOMP_<original-name>.md` (matches T2 pattern in `.doc-tiers.json`).
3. Add a 3-line header to the archived file:
   ```
   > **ARCHIVED YYYY-MM-DD.** This document is no longer current.
   > **Superseded by:** <path-to-new-doc> (or "n/a — completed").
   > **Reason:** <one sentence>.
   ```
4. If 3+ docs are being archived in the same area at once, batch them into a dossier — see `.agents/archiving/DOSSIER_CREATION_TEMPLATE.md`.
5. Update any `.doc-tiers.json` / `.doc-registry.json` references that pointed at the old path.
6. Append to `.agents/DECISION_LOG.md`:
   ```
   YYYY-MM-DD | <agent> | archive | Archived <path> — <reason>
   ```
7. PR title: `[framework] archive <area> docs (YYYY-MM)`.
