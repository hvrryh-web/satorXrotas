[Ver001.000]

# SW-20260524 — Stage 3 Lane Plans

**Status:** Active
**Date opened:** 2026-05-24
**Owner role:** Coordinator
**Spans:** Phase 1 (Months 1–2) implementation
**Source plan (ephemeral):** `/root/.claude/plans/plan-next-stages-to-concurrent-rocket.md`
**Parent docs:** `MASTER_PLAN.md` (Phase 1), `docs/product/ROADMAP.md`, ADR-0009..0014

---

## Why this workplan exists

Captures the detailed lane plans for Stage 3 (Phase-1 implementation) in
the repo so future agent sessions have the canonical reference without
depending on plan-mode local state. The full **execution machinery** —
sequencing, subagent harnesses, success/failure criteria, review cycles —
lives in the plan file referenced above; what follows is the work surface
each lane owns.

## Order of operations (high-level)

Per user-priority order (5 → 3 → 2 → 4 → 1 expanded):

1. **Phase A** — ADR-0015 surface check (orchestrator). Outcome: skip; no new ADR needed.
2. **Phase B** — Commit this workplan to the repo (orchestrator). Outcome: this file.
3. **Phase C** — Lane F first (orchestrator). Tasks F1–F4 land before any feature-lane PR.
4. **Phase D** — Parallel subagent execution: Wave 1 A/B/C/E concurrent; Wave 2 D after E5.
5. **Phase E** — Sovereign per-lane reviews (A → B → C → E → D) with 3-iteration cycles each.

## Cross-lane conventions

- **Branch naming:** `feat/<lane-letter>-<short-name>` (e.g. `feat/a-focus-machine`).
- **PR title:** `[<channel>] <description>` per `.agents/COORDINATION_PROTOCOL.md`.
- **PR scope:** one PR per Task; subtasks may be commits within.
- **Universal success:** typecheck + lint + test + doc-tier-check all green, commit pushed, handoff appended.
- **Gate flip:** always the final Task of each feature lane; CODEOWNER sign-off required.
- **Schema discipline:** `.agents/SCHEMA_REGISTRY.md` updates land in the same PR as the type they describe.

## Lane index

| Lane | Title | Channel | Owner role | Gate | Source ADR(s) |
|------|-------|---------|------------|------|---------------|
| A | `focus-engine` + Focus Hero UI | `packages-engines` + `web-app` | Implementer | `G1.focus-hero` | ADR-0009 |
| B | `audio-engine` + Soundscapes + Deep Canvas | `packages-engines` + `web-app` | Implementer + Designer | `G1.soundscapes` | ADR-0006, ADR-0010 |
| C | `polyworld` Office shell + Asset pipeline | `packages-engines` + `web-app` + `tools/assets/` | Implementer + Designer | `G1.polyworld-office` | ADR-0005, ADR-0012 |
| D | Distraction Blocker (web SW + Chrome MV3 ext) | `web-app` + new `apps/browser-extension/` | Implementer + Critic | `G1.blocker` | ADR-0011 |
| E | `apps/site` content + Auth + Onboarding | `site` + `web-app` | Implementer + Security + Designer | webapp-auth + `G2.premium` (Phase 2) | ADR-0013 |
| F | Coordination (cross-cutting, continuous) | `framework` + `adapters` | Coordinator + Data Engineer | none directly | ADR-0007, ADR-0008, ADR-0014 |

## Dependency graph

```
F ─ continuous ─ unblocks all
                  │
   ┌──────────────┼──────────────┐
   ▼              ▼              ▼
   A              B              E
                                 │
                                 ├─▶ D (calendar OAuth needs E auth)
                                 │
   C ◀── consumes from A/B/D/E ──┘
```

Critical path: **F → E → D**. A, B, C parallelisable after F.

---

## Lane A — `focus-engine` + Focus Hero UI

### Plan
First user-visible RAT-OS feature. XState v5 state machine per ADR-0009; React bindings; Focus Hero module UI (home + active-session full-screen). State survives device sleeps, tab backgrounding, cross-device handoffs. Persistence at session boundaries only — never per-tick. Local-first; countdown re-derives from `Date.now() - startedAt - pausedDuration` each rAF.

### Deliverables
1. `packages/@njz-os/focus-engine/src/machine.ts` — XState v5 actor
2. `packages/@njz-os/focus-engine/src/react.ts` — `useFocusSession` hook
3. `apps/web/src/modules/focus-hero/Home.tsx`, `Active.tsx`, `index.ts`
4. `packages/@njz-os/focus-engine/test/machine.test.ts`
5. `tests/e2e/focus-session.spec.ts`
6. `.agents/PHASE_GATES.md` row flipped OPEN

### Operations
- Daily rebase from `main`; `pnpm --filter @njz-os/focus-engine test --watch` open.
- Dev-only: `@statelyai/inspect` for machine introspection.
- Time-travel in tests via injected `clock` parameter.
- Surfaced design changes → DECISION_LOG; non-trivial → micro-ADR.

### To-Do (8 Tasks × 3 subtasks; see plan file for criteria)
A1. Install XState v5 + scaffold `machine.ts` · A2. Implement state graph per ADR-0009 · A3. Wire vaultbrain persistence boundaries · A4. React bindings (`useFocusSession`) · A5. Module home UI · A6. Active session full-screen · A7. Tests + a11y · A8. Flip `G1.focus-hero` OPEN.

---

## Lane B — `audio-engine` + Soundscapes UI + Deep Canvas Hush

### Plan
Web Audio engine. Gapless stem looping (dual `AudioBufferSourceNode` + 5 s crossfade per ADR-0010); OscillatorNode-pair binaural beats; `AnalyserNode` tapped off master for Deep Canvas Hush. 5 baseline soundscapes ship from `apps/web/public/audio/stems/` (assets via Lane C pipeline). UI exposes category tiles, active player, Deep Canvas full-screen.

### Deliverables
1. `packages/@njz-os/audio-engine/src/engine.ts`, `scheduler.ts`, `binaural.ts`, `deep-canvas.ts`, `quirks/{ios,android}.ts`
2. `apps/web/src/modules/soundscapes/*`
3. 5 baseline soundscape manifests in `apps/web/public/audio/stems/`

### Operations
- `pnpm --filter @njz-os/audio-engine test` watch.
- Every scheduler-touching PR: waveform test verifying ≤ 0.5 dB jump at loop boundary.
- Friday mobile smoke (iPhone 12 + mid-range Android).
- `AudioContext.resume()` always behind a user gesture.

### To-Do (8 Tasks × 3 subtasks)
B1. AudioGraph factory · B2. Stem loader + manifest parser · B3. Gapless crossfade scheduler · B4. Binaural beat generator · B5. Deep Canvas Hush painter · B6. Safety + mobile quirks · B7. Soundscapes module UI · B8. Tests + Lighthouse + gate flip.

---

## Lane C — `polyworld` Office shell + Asset pipeline

### Plan
Canvas 2D isometric renderer for the Office scene per ADR-0005. Owns the asset pipeline per ADR-0012 (Aseprite spritesheets, FFmpeg `loudnorm` audio stems). Decoration unlocks subscribe to the `ProgressionEvent` bus.

### Deliverables
1. `tools/assets/{build-sprites,build-audio,build-manifests,validate-assets}.mjs`
2. `assets/sources/` + `assets/palettes/njz-os.gpl` (shared 32-color palette)
3. `packages/@njz-os/polyworld/src/render-canvas2d.ts`, `scene-loader.ts`
4. `packages/@njz-os/pixel-art/src/loader.ts`
5. Baseline asset set (~50 tiles + ~20 decorations + hero sprite)
6. `apps/web/src/modules/polyco-world/Office.tsx`

### Operations
- `pnpm assets:validate` in CI + locally before push.
- Designer commits `.aseprite` + `.wav` to `assets/sources/`; CI regenerates `public/` artefacts.
- File-size budgets enforced by validator (sprites < 500 KB, stems < 10 MB, total audio < 200 MB).
- Off-palette colours blocked by validator.

### To-Do (7 Tasks × 3 subtasks)
C1. Asset pipeline scripts · C2. Shared palette + seed asset set · C3. Pixel-art sprite loader · C4. Canvas 2D isometric renderer · C5. Scene graph + decoration system · C6. Office scene + ProgressionEvent subscription · C7. Module UI + tests + gate flip.

---

## Lane D — Distraction Blocker

### Plan
Two-tier Phase-1 blocker per ADR-0011. Tier 1: in-app service worker (RAT-OS origin only, always-on). Tier 2: opt-in Chrome MV3 browser extension using `declarativeNetRequest`. Calendar OAuth read-only (Google + Apple) for auto-scheduling. Native iOS/Android deferred to Phase 3.

### Deliverables
1. `apps/web/src/sw.ts`
2. `apps/web/src/modules/distraction-blocker/*`
3. `apps/browser-extension/` (new workspace package, MV3)
4. `packages/@njz-os/focus-engine/src/blocker.ts` extended schedule resolver
5. Calendar OAuth flow (shared with Lane E)

### Operations
- SW testing: Playwright with service-worker context enabled.
- Extension testing: headless Chromium "Load unpacked".
- Coordination with Lane E: OAuth origin shares Supabase Auth domain.
- Chrome Web Store review tail 1–3 weeks; flag in plan early.

### Dependency
**Launches in Wave D.2 only after Subagent E signals "E5 DONE"** in its handoff.

### To-Do (7 Tasks × 3 subtasks)
D1. Schedule resolver · D2. Service worker enforcement (Tier 1) · D3. Block-list UI · D4. Browser extension (Tier 2) · D5. Calendar integration shell · D6. Focus-engine coupling + analytics · D7. Tests + extension submission + gate flip.

---

## Lane E — `apps/site` content + Auth + Onboarding

### Plan
Marketing site full content (Next.js SSG/ISR) + Supabase Auth wiring (passkeys + email magic-link per ADR-0013) + 3-step onboarding wizard. Auth unblocks Lane D (calendar OAuth) and Phase 2 premium billing.

### Deliverables
1. `apps/site/src/app/(marketing)/*` — full content
2. `packages/adapters/identity-client/src/*` — real Supabase wiring (replaces stub)
3. `apps/web/src/auth/*` — webapp auth shell + tier check
4. `apps/web/src/onboarding/*` — 3-step wizard
5. `apps/web/src/account/*` — settings + Right-to-Delete

### Operations
- Separate Supabase `preview` project (no prod credential pollution).
- Designer reviews each iteration in mobile + desktop viewports.
- Security review on every auth-touching PR per `.agents/CONTEXT_SECURITY.md`.
- detect-secrets baseline refreshed on credential rotation.

### To-Do (8 Tasks × 3 subtasks)
E1. Marketing site content · E2. About + blog scaffold · E3. Supabase Auth wiring · E4. Passkey + email sign-in UX · E5. Webapp shell + tier check **← Wave D.2 gate** · E6. Onboarding wizard · E7. Account settings + Right-to-Delete · E8. Security review + a11y + launch readiness.

---

## Lane F — Coordination (cross-cutting, continuous)

### Plan
Non-feature lane. Files upstream issues per `.agents/active/upstream-coordination.md`, vendors agent-gateway openapi.json per ADR-0014, maintains `contracts/openapi/njz-rat-os.yaml` sync, runs monthly cleanup, flips phase gates as feature lanes close their final tasks.

### Deliverables
1. Upstream issue: `@njz/ui` publish (ADR-0007 follow-through)
2. Upstream issue: vaultbrain extension (ADR-0008 Option A)
3. `contracts/openapi/agent-gateway.yaml` vendored
4. `tools/contracts/refresh-agent-gateway.mjs` + `.github/workflows/contracts-drift.yml`
5. Weekly-updated PHASE_GATES + DECISION_LOG + PROJECT_STATUS_OVERVIEW
6. `docs/dev-reports/DR-0002-phase-1-launch.md` at Phase 1 close

### Operations
- **Weekly (Friday):** tour `.agents/active/upstream-coordination.md`; bump thread statuses.
- **Monthly (1st Friday):** `docs/ai-operations/MONTHLY_CLEANUP_PROTOCOL.md` end-to-end.
- **Per gate flip:** CODEOWNER sign-off → DECISION_LOG → PHASE_GATES → logbook entry.

### To-Do (8 Tasks × 3 subtasks)
F1. File @njz/ui upstream issue · F2. File vaultbrain extension upstream issue · F3. Vendor agent-gateway openapi.json · F4. Weekly contracts-drift CI workflow · F5. Maintain consumer openapi.yaml · F6. Monthly cleanup protocol · F7. Phase gate management · F8. Phase-1 retro + DR-0002.

---

## Stage 3 exit criteria

- All `G1.*` gates `OPEN` in `.agents/PHASE_GATES.md`.
- Each lane's task-umbrella PRs merged.
- `pnpm test:e2e` covers one full end-to-end smoke (focus session → decoration unlock → vaultbrain sync).
- Lighthouse perf + a11y + PWA ≥ 85 on `apps/web` main routes.
- `docs/dev-reports/DR-0002-phase-1-launch.md` merged.
- `MASTER_PLAN.md` advanced to Phase 2.

## See also

- Full execution machinery (subagent harnesses, criteria, review cycles): plan file at `/root/.claude/plans/plan-next-stages-to-concurrent-rocket.md` (ephemeral).
- ADRs: `docs/architecture/ADR/ADR-0005..0014.md`.
- Prototype-system specs: `docs/prototype-systems/PS-001..PS-007.md`.
- Coordination thread: `.agents/active/upstream-coordination.md`.
- Schema registry: `.agents/SCHEMA_REGISTRY.md`.
- Coordination protocol: `.agents/COORDINATION_PROTOCOL.md`.
