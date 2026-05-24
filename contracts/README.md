# contracts/

Pure schema. No code. The contract surface between RAT-OS and the upstream platform (`notbleaux/ZeSporteXte`).

## Members

```
openapi/
  njz-rat-os.yaml          # OpenAPI 3.1 — the REST surface RAT-OS depends on
events/
  progression-events.json  # Canonical event taxonomy (progression, session, streak)
schemas/
  README.md                # Where shared JSON schemas live (TBD)
```

## Rules

- Schemas are versioned. Breaking changes need an ADR.
- The upstream owns the canonical types; we mirror only what we use.
- Generated artifacts (typed clients) live in `packages/adapters/<service>-client/src/generated/` and are committed.
