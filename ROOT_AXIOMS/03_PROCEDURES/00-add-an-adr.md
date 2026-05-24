[Ver001.000]

# PROC-00 — Add an ADR

1. Run `pnpm adr:new "Title"` (scaffolds at `docs/architecture/ADR/ADR-XXXX-<slug>.md`).
2. Fill in:
   - **Context** (3-6 sentences)
   - **Decision** (the action)
   - **Status** = `Proposed`
   - **Consequences** (positive + negative)
   - **Alternatives Considered** (3+ alternatives, why rejected)
3. Open PR. Title: `[architecture] ADR-XXXX <title>`.
4. On CODEOWNER approval, change `Status: Proposed` → `Status: Accepted` in a follow-up commit.
5. Append a one-line entry to `.agents/DECISION_LOG.md`:
   ```
   YYYY-MM-DD | <agent> | architecture | <one-sentence decision> → ADR-XXXX
   ```
6. Cross-reference from any related docs (`.agents/SCHEMA_REGISTRY.md`, prototype-system specs, etc.).
