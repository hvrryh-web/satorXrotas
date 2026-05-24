[Ver001.000]

# CHARTER — ROOT_AXIOMS

## Purpose

`ROOT_AXIOMS/` exists so that recurring decisions don't get re-litigated in every PR. Anything *true at the project level* (not the file level) lives here.

## Scope

In scope: principles, standards, procedures, references — anything that applies repo-wide.

Out of scope: per-module configuration, per-feature design, ephemeral decisions.

## Governance

- **Owner role:** Coordinator.
- **Change process:** ADR + CODEOWNER review + DECISION_LOG entry.
- **Versioning:** every file carries `[VerMMM.mmm]`. Bump `MMM` for breaking, `mmm` for additive.
- **Review cadence:** quarterly; flag staleness if no review in 90 days.

## Numbering Convention

Files in `01_PRINCIPLES/`, `02_STANDARDS/`, `03_PROCEDURES/` use a 2-digit prefix for ordering:

```
01_PRINCIPLES/
  00-charter.md
  01-product-thesis.md
  02-engineering-ethos.md
  ...
```

The prefix has no semantic meaning beyond display order. References (04) are filed by topic, not number.
