[Ver001.000]

# ROOT_AXIOMS

The invariants. Things that should be true across every phase, every module, every commit. Ordered from most abstract (principles) to most concrete (references).

```
00_META/         How the axioms themselves are governed
01_PRINCIPLES/   Product, design, engineering principles
02_STANDARDS/    Code, doc, naming, accessibility standards
03_PROCEDURES/   How to do common operations correctly
04_REFERENCES/   External authorities we defer to
```

## How To Use

- When in doubt about *what* to do → read principles.
- When unsure *how* to do it correctly → read standards.
- When you've decided what + how, but need a step-by-step → read procedures.
- When you need to cite an external source → reference here first.

## Editing Axioms

Changes to anything in `ROOT_AXIOMS/` require:

1. An ADR.
2. Sign-off from a CODEOWNER.
3. A `DECISION_LOG.md` entry.

Axioms are not opinions; they are the agreements we don't want to relitigate every PR.
