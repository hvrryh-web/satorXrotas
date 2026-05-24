[Ver001.000]

# Governance Decision Log

This file mirrors `.agents/DECISION_LOG.md` for *governance-level* decisions specifically — agent contracts, phase gates, doc tier policies, framework changes. Technical decisions stay in `.agents/DECISION_LOG.md`.

Format:

```
YYYY-MM-DD | <decision-maker> | <topic> | <one-sentence decision>
```

---

2026-05-24 | @hvrryh-web | framework | Adopted NJZPOF v0.2 framework for RAT-OS (mirrors notbleaux/ZeSporteXte conventions).
2026-05-24 | @hvrryh-web | naming | Brand = "NJZ RAT-OS"; technical = "NJZ-OS" / "@njz-os/*".
2026-05-24 | @hvrryh-web | preservation | Prior repo contents preserved on branch legacy/satire-deck-veritas; immutable.
2026-05-24 | @hvrryh-web | integration | RAT-OS consumes notbleaux/ZeSporteXte via @njz/* npm + HTTP/WS adapters; no submodule, no fork.
2026-05-24 | @hvrryh-web | scope | Phase 0 scope: framework + monorepo skeleton + docs + ADR-0001..0006. No feature code.
