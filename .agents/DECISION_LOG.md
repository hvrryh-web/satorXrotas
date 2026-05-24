[Ver001.000]

# DECISION_LOG — NJZ RAT-OS

Append-only chronological log of substantive decisions. One line per decision. For deep rationale, link to an ADR.

Format:

```
YYYY-MM-DD | <agent> | <area> | <one-sentence decision> [→ ADR-XXXX]
```

---

2026-05-24 | claude-opus-4.7 | bootstrap | Adopted NJZ RAT-OS as brand and NJZ-OS as technical namespace → ADR-0001
2026-05-24 | claude-opus-4.7 | bootstrap | Selected pnpm + Turborepo monorepo (matches upstream ZeSporteXte) → ADR-0001
2026-05-24 | claude-opus-4.7 | integration | Consume ZeSporteXte services via @njz/* npm scope and HTTP/WS, no submodule, no fork → ADR-0002
2026-05-24 | claude-opus-4.7 | state | Vaultbrain is the persistent state backend; reach via adapters layer, never directly → ADR-0003
2026-05-24 | claude-opus-4.7 | apps | Split into apps/site (Next.js 15 marketing) and apps/web (Vite + React 19 webapp); different runtimes, shared tokens → ADR-0004
2026-05-24 | claude-opus-4.7 | rendering | PolyCo.World renders via HTML5 Canvas 2D for v0; WebGL behind feature flag for later → ADR-0005
2026-05-24 | claude-opus-4.7 | audio | Web Audio API as the base; binaural beats via OscillatorNode pair with stereo separation; soundscapes via gapless looping of 5-min stems → ADR-0006
2026-05-24 | claude-opus-4.7 | framework | Adopted NJZPOF v0.2 from upstream (`.agents/`, `ROOT_AXIOMS/`, `.doc-tiers.json`, `.doc-registry.json`) with RAT-OS-specific contents
2026-05-24 | claude-opus-4.7 | preservation | Preserved prior Satire-deck-Veritas restructure on branch `legacy/satire-deck-veritas` before wiping main
2026-05-24 | claude-opus-4.7 | stage-0 | Verified Phase 0 skeleton compiles + lints + tests + builds end-to-end on Node 20; ESLint migrated to v9 flat config; package tsconfig path-inheritance bug fixed
2026-05-24 | claude-opus-4.7 | integration | Reality-check: upstream `packages/@njz/ui` has no package.json — defer `@njz/ui` consumption until upstream publishes a real package + semver tag + initial primitive set; `@njz-os/ui` stays self-contained for Phase 1 → ADR-0007 (Accepted)
2026-05-24 | claude-opus-4.7 | state | Reality-check: upstream `services/vaultbrain` is a multi-vault note system, not a user-state backend — extend vaultbrain upstream with users/sessions/streaks/progression_events/cognitive_profiles tables + endpoints + Redis WS pub/sub; supersedes ADR-0003; fallback Option B documented → ADR-0008 (Accepted)
2026-05-24 | @hvrryh-web | framework | Approved PR #19 — RAT-OS bootstrap + Stage 0 closeout + ADR-0007 + ADR-0008 land on main
