[Ver001.000]

# PHASE-0 LOGBOOK — Foundation

**Opened:** 2026-05-24
**Status:** active
**Exit criteria:** see `MASTER_PLAN.md` § "Phase 0 Exit Criteria"

---

## 2026-05-24 — Phase opened

NJZ RAT-OS bootstrapped:

- Brand decided: `NJZ RAT-OS` (marketing) / `NJZ-OS` (technical).
- Integration model: shared `@njz/*` scope + HTTP/WS adapters into ZeSporteXte services.
- Repo wipe + structure rebuild on `claude/gracious-mayer-Emj1S`.
- Legacy contents preserved at `legacy/satire-deck-veritas`.

ADRs filed (all Status: Accepted):

- ADR-0001 — Monorepo structure + brand naming
- ADR-0002 — Consume @njz/* packages (loose coupling)
- ADR-0003 — Vaultbrain as state backend
- ADR-0004 — apps/site (Next.js) vs apps/web (Vite + React) split
- ADR-0005 — PolyCo.World renderer: HTML5 Canvas 2D v0, WebGL behind flag
- ADR-0006 — Audio engine: Web Audio API + OscillatorNode pair for binaural

Dev report DR-0001 filed documenting bootstrap.

PS-001..PS-007 module specs drafted (status: Draft for all; flipped to Approved per-module when each Phase 1+ gate opens).

Skeleton compiles (placeholder content); CI workflow in place.

**Next:** human review + merge to `main`. Phase 0 exit gate flips on merge.
