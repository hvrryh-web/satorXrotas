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
2026-05-24 | claude-opus-4.7 | focus | Focus Engine state machine: XState v5; modes pomodoro_25_5 / deep_work_50_10 / sprint_15_3 / flow_90_20; timestamp-based drift handling; persistence at session boundaries only → ADR-0009 (Accepted)
2026-05-24 | claude-opus-4.7 | audio | Audio Engine v0 detail: dual-AudioBufferSource crossfade per stem; OscillatorNode pair through StereoPanner for binaural; AnalyserNode tapped off master for Deep Canvas FFT; DynamicsCompressor brick-wall limiter → ADR-0010 (Accepted)
2026-05-24 | claude-opus-4.7 | blocker | Distraction Blocker: two-tier (in-app service worker + Chrome MV3 browser extension) for Phase 1; native iOS/Android deferred to Phase 3; honest marketing copy → ADR-0011 (Accepted)
2026-05-24 | claude-opus-4.7 | assets | Asset pipeline: Aseprite → spritesheets; FFmpeg loudnorm → AAC + Ogg; shipped from apps/web/public/ in Phase 1; Cloudflare R2 in Phase 2; CI validator guards orphan/oversized assets → ADR-0012 (Accepted)
2026-05-24 | claude-opus-4.7 | auth | Auth model: passkeys (WebAuthn) primary + email magic-link fallback via Supabase Auth; tier source-of-truth in vaultbrain, identity in Supabase; OAuth scope future-compatible with calendar integration → ADR-0013 (Accepted)
2026-05-24 | claude-opus-4.7 | contracts | Vendor `services/agent-gateway/openapi.json` as `contracts/openapi/agent-gateway.yaml` at pinned upstream SHA; weekly drift detection workflow; consumer codegen behind G4.ai-personalization → ADR-0014 (Accepted)
2026-05-24 | @hvrryh-web | architecture | Approved PR #20 — Stage 2 Phase-1 module ADRs (0009-0014) land on main
2026-05-24 | claude-opus-4.7 | architecture | ADR-0015 surface check: SKIP — no new ADR needed. Candidates (apps/browser-extension location, G1.webapp-auth new gate, subagent-orchestration pattern) are either covered by existing ADRs (0011 for extension), operational not architectural (new gate row), or belong in `.agents/` framework (orchestration). Phase A of the Stage 3 sequenced execution complete.
2026-05-24 | claude-opus-4.7 | framework | Captured Stage 3 lane plans in repo at `.agents/session-workplans/SW-20260524-stage-3-lanes.md`; full execution machinery (subagent harnesses, success/failure criteria, review cycles) remains in plan file. Phase B complete.
2026-05-24 | claude-opus-4.7 | coordination | Lane F Task F1: filed upstream `@njz/ui` publish issue at notbleaux/ZeSporteXte#117 per ADR-0007 follow-through.
2026-05-24 | claude-opus-4.7 | coordination | Lane F Task F2: filed upstream vaultbrain extension issue at notbleaux/ZeSporteXte#118 per ADR-0008 Option A; 2-week timer to 2026-06-07 for Option B fallback.
2026-05-24 | claude-opus-4.7 | contracts | Lane F Task F3: vendored agent-gateway openapi.json as contracts/openapi/agent-gateway.yaml at upstream SHA 22131186e5b179a73e90bbe98dacc85fb558765f; refresh script at tools/contracts/refresh-agent-gateway.mjs; pnpm contracts:refresh-agent-gateway wired.
2026-05-24 | claude-opus-4.7 | ci | Lane F Task F4: weekly contracts-drift workflow at .github/workflows/contracts-drift.yml; informational drift issue on non-empty diff; runbook at docs/operations/RUNBOOKS/contracts-drift.md.
2026-05-24 | claude-opus-4.7 | orchestration | Phase D Wave 1 attempted with 4 concurrent Agent calls (lanes A/B/C/E, worktree-isolated, background). All four hit session token limits within ≤102 s, returning ≤1.8 K tokens each with zero commits produced. Branches feat/{a,b,c,e}-stage-3 were created but pointed at b380dde (main HEAD) with no advance. Cleaned up: branches deleted, empty .claude/worktrees/ removed, main restored as the checked-out branch. Added `.claude/` to .gitignore to prevent recurrence. Phase D paused pending fresh-session retry (session limit resets 23:30 UTC).
2026-05-24 | claude-opus-4.7 | hygiene | Added `.claude/` to .gitignore — Claude Code subagent worktrees are transient and must never be committed; stop-hook caught this on the prior session.
