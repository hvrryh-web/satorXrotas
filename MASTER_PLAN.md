[Ver001.000]

# MASTER PLAN — NJZ RAT-OS

**Phase:** 0 — Foundation
**Status:** Active (just bootstrapped)
**Owner:** @hvrryh-web
**Last revised:** 2026-05-24

---

## Mission

Ship `NJZ RAT-OS` — a single, cohesive web + webapp surface that integrates the seven NJZ-OS modules and the PolyCo.World metaverse into one progression loop. Funding constraint: **$0 infrastructure budget** for MVP (per uploaded Build Plan). Engineering posture: **AI-orchestrated** with the same NJZPOF v0.2 framework used in the upstream platform.

## Six-Month Outcome (from PRD §2.3.3)

| Month | Deliverable |
|-------|-------------|
| 1–2 | Phase 0 framework live; Phase 1 MVP web (Focus Hero + Soundscapes + Blocker + PolyCo Office shell) → 5,000 MAU |
| 3–4 | Phase 2: Brain Training, Writing Space, Micro-Learning, PolyCo Home; mobile PWA → 25,000 MAU |
| 5–6 | Phase 3: Social, seasonal events, native apps → 75,000 MAU |

## Current Phase: Phase 0 — Foundation

**Goal:** establish the canonical AI-orchestration framework, monorepo skeleton, and integration contracts with ZeSporteXte before any feature code is written.

### Phase 0 Workstreams

1. **Framework** — `.agents/`, `ROOT_AXIOMS/`, `.doc-tiers.json`, `.doc-registry.json`, `CLAUDE.md`, `AGENTS.md`.
2. **Docs** — refined PRD, OKRs, market review, personas, roadmap, ADR-0001..0006, dev report DR-0001, prototype-system specs PS-001..007.
3. **Monorepo** — pnpm workspace, turborepo, tsconfig.base, eslint/prettier configs, CI workflow.
4. **App skeletons** — `apps/site` (Next.js placeholder), `apps/web` (Vite placeholder with 7 module route stubs).
5. **Package skeletons** — `packages/@njz-os/{core,ui,audio-engine,focus-engine,polyworld,pixel-art,progression,analytics,learning-cards,writing,tsconfig}`.
6. **Adapters** — typed-client scaffolds for vaultbrain, agent-gateway, api, identity.
7. **Contracts** — `contracts/openapi/njz-rat-os.yaml` (initial surface), `contracts/events/progression-events.json`.
8. **Infra** — Vercel/Render config stubs, Docker compose for local dev (Postgres + Redis pointed at upstream-compatible images).

### Phase 0 Exit Criteria

- [ ] All workstreams 1–8 merged on `main`.
- [ ] `pnpm install && pnpm build` succeeds with placeholder content.
- [ ] `pnpm typecheck` passes with zero errors.
- [ ] `.doc-tiers.json` validation passes; no orphan root `.md` files.
- [ ] ADR-0001 through ADR-0006 all `Status: Accepted`.
- [ ] DR-0001 (bootstrap dev report) merged.
- [ ] One end-to-end smoke route in `apps/web` renders without errors.

### Phase Gates

See `.agents/PHASE_GATES.md` for the formal gate definitions. Phase 1 (Focus Hero + Soundscapes + Blocker) does not unlock until Phase 0 exit criteria are all met.

---

## Out of Phase 0 Scope (Defer)

- Any module business logic (focus timer behavior, audio playback, PolyCo rendering).
- Real-time WebSocket integration with vaultbrain.
- Authentication / identity flow.
- Premium subscription billing.
- Mobile-native shells (Capacitor / Tauri / RN).
- Pixel-art asset pipeline.
- Production deployment to Vercel / Render.

These all live behind explicit Phase 1+ gates.

---

## Risk Register (Phase 0)

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Drift from ZeSporteXte conventions | M | H | Mirror `.agents/`, `.doc-tiers.json`, ROOT_AXIOMS structure exactly; review with upstream owners |
| `@njz/*` package surface changes upstream | M | M | Lock to specific versions; adapters layer absorbs change; integration tests at adapter boundary |
| Scope creep (someone tries to ship a module in Phase 0) | H | M | PHASE_GATES.md gate enforcement in CI |
| Multiple agents stepping on each other | H | M | COORDINATION_PROTOCOL.md channels + session workplans |

---

## Dependencies

- **Upstream:** `notbleaux/ZeSporteXte` for `@njz/ui`, `services/vaultbrain`, `services/agent-gateway`, `services/api`.
- **External:** Vercel (site), Render or Fly.io (BFF), Cloudflare R2/Supabase for asset hosting (Phase 2+).

---

## Reference

- Uploaded PRDs (3× duplicate `NJZOS_PRD.docx`) — synthesized into `docs/product/PRD.md`.
- Uploaded `3NJZOS_Build_Plan.docx` — synthesized into `docs/product/ROADMAP.md` + `docs/operations/DEPLOYMENT.md`.
- Uploaded `3NJZOS_Market_Review.docx` — synthesized into `docs/product/MARKET_REVIEW.md`.
- Upstream platform repo: `notbleaux/ZeSporteXte`.
- Legacy preserved at branch: `legacy/satire-deck-veritas` (do not delete).
