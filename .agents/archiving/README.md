# .agents/archiving/

How and when to retire a document. Pairs with the doc-tier system (`.doc-tiers.json`).

```
DOSSIER_CREATION_TEMPLATE.md  # Template for batching multiple stale docs into a single dossier
```

Default convention: prefix archived files with `xCOMP_` and move them under `archive/<area>/<year>/`. Once moved, drop them from T0/T1 in `.doc-tiers.json` (they auto-match the T2 `xCOMP_*` pattern).
