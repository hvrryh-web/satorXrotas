[Ver001.000]

# Drift Closure SLA — NJZ RAT-OS

"Drift" = the gap between what `MASTER_PLAN.md` / ADRs say is true and what the code actually does. Drift is normal; un-closed drift is not.

## Drift Categories

| Severity | Description | SLA to closure |
|----------|-------------|----------------|
| Critical | Production breakage; security regression; data loss risk | < 24 hours |
| High | Phase-gate violation; ADR contradiction in `main`; doc-tier rule violation | < 7 days |
| Medium | Schema mismatch between `.agents/SCHEMA_REGISTRY.md` and code; stale dev report | < 14 days |
| Low | Cosmetic drift; outdated examples in docs; broken external link | < 30 days |

## Detection

- CI catches: doc-tier violations, boundary violations, broken tests.
- Manual catches: code review, monthly cleanup.
- Agent catches: anything noticed during a session — surface immediately.

## Closure

- Critical: open a fix PR within the SLA window; if can't fix, escalate to user.
- High: open an issue + PR; if upstream-blocked, log in `.agents/active/`.
- Medium / Low: batch into a weekly hygiene PR (`[framework] hygiene <yyyy-mm-dd>`).

## Tracking

- Open drift items live in `.agents/active/drift-<yyyy-mm>.md`.
- Closed drift items are referenced from the relevant PR + `.agents/DECISION_LOG.md` on closure.

## When Drift Won't Close

Two patterns to watch:

1. **Recurring drift in the same area.** Indicates a stale ADR or missing automation. File a meta-issue.
2. **Drift the user keeps deferring.** Acceptable in the short term; revisit at every phase-close retro. Eventually, either close it or update the spec to match reality.
