[Ver001.000]

# FILTER_RULES — selective reading

When a doc is large and your context budget is small, use these rules.

## Universal

- Always read the version header `[VerMMM.mmm]` and any explicit `Status:` line.
- Always read the first H2 ("##") section — usually the abstract / purpose.
- Always read any "Out of scope" or "Do not" section.

## PRD

- Tables of KPIs: read in full.
- Module deep-dives: read only the one relevant to your task.
- Citations `[^N^]`: skip on first pass; fetch when you need to justify a number.

## ADRs

- Read **Context → Decision → Consequences** sections.
- Skip **Alternatives Considered** unless you're writing a counter-ADR.

## Phase plans / logbooks

- Read entries from the last 2 weeks.
- Skim older entries; jump to the linked ADR if a decision is referenced.

## Prototype-system specs (PS-XXX)

- Read **Status / Interfaces / Risks**.
- Skip the rendering/audio implementation notes unless you're implementing.

## Schema registry

- Search by type name first. Only load the surrounding section if you need to understand its package's purpose.

## Phase logbook

- Read only the last opened phase entry unless writing a retrospective.
