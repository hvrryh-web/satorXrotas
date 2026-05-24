[Ver001.000]

# STD-01 — Documentation Standards

## Every canonical doc has

1. Version header `[VerMMM.mmm]` on line 1.
2. H1 title on line 2 (`# TITLE`).
3. Status line if applicable (`Status: Active / Draft / Accepted / Deprecated`).
4. One-paragraph purpose statement.

## Tone

- Direct. Active voice. Present tense.
- Second person ("you") for guides; third person ("the system") for specs.
- No marketing fluff in technical docs.

## Length

- A doc should answer one question well, not three questions poorly.
- If a section grows beyond 5 paragraphs, consider splitting.
- Long is fine when content is dense; bloat is not.

## Headings

- ATX style (`#`, `##`, ...).
- Sentence case.
- Each H2 starts a section the reader could read in isolation.

## Links

- Internal: relative paths (`docs/architecture/ADR/ADR-0001-monorepo-structure.md`).
- External: full URLs.
- Anchor links: when targeting a section, include the slug (`MASTER_PLAN.md#phase-0`).

## Code Blocks

- Always specify language.
- Trim trailing whitespace.

## Tables

- Use them when comparing 3+ items across 2+ attributes.
- Don't use them for "label: value" pairs (use a definition list instead).

## Versioning

- Increment `MMM` (major) for breaking content changes — readers must reread.
- Increment `mmm` (minor) for additive / clarifying edits.
- Don't bump for typo fixes.

## Approved Root .md Files

The canonical list is in `.doc-tiers.json` → `manifest.approved_root_files`. CI fails on root `.md` files not in the list. Add deliberately.

## Cross-References

When you cite another doc, link it. When you cite an external source, link + add a short attribution.

## ADRs

Use the template in `docs/governance/ADR_TEMPLATE.md`. Mandatory sections:

- Context
- Decision
- Status (`Proposed`, `Accepted`, `Deprecated`, `Superseded by ADR-NNNN`)
- Consequences
- Alternatives Considered

## Dev Reports

Use the template in `docs/dev-reports/TEMPLATE.md`. Mandatory sections:

- Summary (3 sentences max)
- What changed
- Why
- Verification
- Follow-ups
