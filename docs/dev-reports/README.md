# Dev Reports (DR-XXXX)

Engineering retrospectives. Each substantive piece of work — a major feature, a refactor, a phase close, a post-mortem — gets a dev report.

## Convention

- Filename: `DR-XXXX-<kebab-slug>.md`. Four digits, zero-padded, monotonic.
- Use `TEMPLATE.md` as the starting point.

## Required Sections

1. **Summary** (3 sentences max)
2. **What changed**
3. **Why**
4. **Verification**
5. **Follow-ups**

## When To Write One

- After closing a phase.
- After shipping a feature that an end user notices.
- After a non-trivial refactor.
- After a production incident (post-mortem variant).
- After completing a quarterly OKR cycle.

Optional but encouraged for ADR-implementing PRs that turned out interestingly different from the ADR's prediction.

## Index

| ID | Title | Date | Status |
|----|-------|------|--------|
| DR-0001 | Bootstrap — Phase 0 reconstruction | 2026-05-24 | Merged |
