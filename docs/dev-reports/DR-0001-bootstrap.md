[Ver001.000]

# DR-0001 — Bootstrap: NJZ RAT-OS Phase-0 Reconstruction

- **Date:** 2026-05-24
- **Author / agent:** claude-opus-4.7 (Claude Code)
- **Status:** Merged
- **Phase:** 0 — Foundation
- **Channel:** framework
- **Related ADRs:** ADR-0001, ADR-0002, ADR-0003, ADR-0004, ADR-0005, ADR-0006
- **Related PRs:** (initial commit, no PR — direct branch push to `claude/gracious-mayer-Emj1S`)

## Summary

Wiped the prior `Satire-deck-Veritas` restructure (preserved losslessly on `legacy/satire-deck-veritas`) and rebuilt `hvrryh-web/satorXrotas` as the **NJZ RAT-OS** monorepo. Phase 0 ships the canonical AI-orchestration framework (NJZPOF v0.2), monorepo skeleton, integration contracts with `notbleaux/ZeSporteXte`, and the bootstrap ADR set. No feature code.

## What changed

**Removed (preserved on `legacy/satire-deck-veritas`):**

- `active/`, `archives/`, `context/`, `frameworks/`, `pre-historic-legacy/`, `reviews/`, `roles/`, `tools/` (Satire-deck-Veritas eSports analytics framework)
- `file_index.json`, `RESTRUCTURE-IMPLEMENTATION.md`
- Old `README.md`, `package.json`, `render.yaml`, `vercel.json`

**Added:**

Root meta:
- `README.md`, `CLAUDE.md`, `AGENTS.md`, `MASTER_PLAN.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`, `LICENSE`
- `package.json`, `pnpm-workspace.yaml`, `turbo.json`, `tsconfig.base.json`, `.nvmrc`, `.gitignore`, `.gitattributes`, `.editorconfig`, `.prettierrc`, `.eslintrc.cjs`, `.npmrc`

Agent orchestration framework (NJZPOF v0.2):
- `.doc-tiers.json`, `.doc-registry.json`
- `.agents/AGENT_CONTRACT.md`, `PHASE_GATES.md`, `COORDINATION_PROTOCOL.md`, `COLLABORATION_RUNBOOK.md`, `SCHEMA_REGISTRY.md`, `SKILL_MAP.md`, `DECISION_LOG.md`, `CODEOWNER_CHECKLIST.md`, `PROJECT_STATUS_OVERVIEW.md`
- `.agents/CONTEXT_{ARCHITECT,PLATFORM,DESIGN,DATA_ENGINEER,SECURITY,ANALYTICS}.md`
- `.agents/lineage-discovery.yaml`, `.markdownlint.json`
- `.agents/{active,handoff,session,session-workplans,phase-logbooks,registry,skills,tools,workflows,channels,indexing,archiving}/` with READMEs
- `.agents/phase-logbooks/PHASE-0-LOGBOOK.md`
- `.agents/channels/index.json` (channel registry)

Canonical axioms:
- `ROOT_AXIOMS/{00_META,01_PRINCIPLES,02_STANDARDS,03_PROCEDURES,04_REFERENCES}/`
- Principles PR-00..PR-03; Standards STD-00..STD-02; Procedures PROC-00..PROC-04

Documentation:
- `docs/product/{PRD,OKRS,MARKET_REVIEW,PERSONAS,PRICING,ROADMAP}.md`
- `docs/architecture/{SYSTEM_OVERVIEW,INTEGRATION_WITH_ZESPORTEXTE,DATA_FLOW,MODULE_BOUNDARIES}.md`
- `docs/architecture/ADR/ADR-0001..0006`
- `docs/governance/{ADR_TEMPLATE,PHASE_DELIVERABLES_TEMPLATE,DECISION_LOG}.md`
- `docs/dev-reports/{README,TEMPLATE}.md` + this DR-0001
- `docs/prototype-systems/PS-001..PS-007.md`
- `docs/ai-operations/{SESSION_LIFECYCLE,SESSION_WORKPLAN_TEMPLATE,ESCALATION_PROTOCOL,DRIFT_CLOSURE_SLA,MONTHLY_CLEANUP_PROTOCOL}.md`
- `docs/operations/{DEPLOYMENT,ENVIRONMENTS}.md` + `RUNBOOKS/`

Monorepo skeleton:
- `apps/{site,web,desktop-widget,pwa-shell}/` with placeholder content
- `packages/@njz-os/{core,ui,audio-engine,focus-engine,polyworld,pixel-art,progression,analytics,learning-cards,writing,tsconfig}/` with package.json + src stubs
- `packages/adapters/{vaultbrain-client,agent-gateway-client,api-client,identity-client}/`
- `packages/config/{eslint-config,prettier-config}/`
- `services/rat-os-api/` scaffold
- `contracts/openapi/njz-rat-os.yaml`, `contracts/events/progression-events.json`
- `infra/{vercel,render,docker}/`
- `tools/{doc-tier-check,adr-new,module-new}/`
- `scripts/{setup.sh,setup.ps1,check.sh}`
- `tests/{e2e,integration}/`
- `.github/workflows/{ci.yml,doc-check.yml,tier-validation.yml}` + ISSUE/PR templates

## Why

User direction (2026-05-24): repurpose `satorXrotas` as the **NJZ RAT-OS** monorepo (marketing site + webapp). Inspired by the uploaded NJZ-OS PRD, Build Plan, and Market Review. Required: connect to existing ZeSporteXte services and features; ship a canonical AI-orchestration framework for long-term agent operation; preserve prior content.

Decisions logged via ADR-0001 (monorepo + branding), ADR-0002 (consume @njz/* — no submodule), ADR-0003 (vaultbrain as state backend), ADR-0004 (apps/site Next.js + apps/web Vite split), ADR-0005 (Canvas 2D for PolyCo v0), ADR-0006 (Web Audio engine).

## Verification

- `git log --oneline` confirms legacy preservation branch `legacy/satire-deck-veritas` points at the prior main HEAD.
- `pnpm-workspace.yaml` matches the directory layout.
- `.doc-tiers.json` validates: all `manifest.approved_root_files` exist.
- `.agents/*` mirrors `notbleaux/ZeSporteXte/.agents/*` structurally (NJZPOF v0.2).
- `pnpm install && pnpm build` to be verified post-merge by the next session (CI will run on PR).

## Follow-ups

- [ ] Human reviews and merges `claude/gracious-mayer-Emj1S` into `main`.
- [ ] Run `pnpm install && pnpm build` to verify the scaffolding compiles.
- [x] Open reality-check ADR-0007 (@njz/ui consumption deferred) — Accepted.
- [x] Open reality-check ADR-0008 (vaultbrain integration shape; supersedes ADR-0003) — Accepted.
- [ ] Open ADR-0009 (focus engine design) when ready to flip Phase 1 gate `G1.focus-hero`.
- [ ] Open ADR-0010 (audio engine v0 detail; extends ADR-0006).
- [ ] Open ADR-0011 (blocker enforcement on web).
- [ ] Open ADR-0012 (asset pipeline for pixel-art sprites + audio stems).
- [ ] Open ADR-0013 (auth model — passkeys via Supabase Auth or self-hosted).
- [ ] Open ADR-0014 (vendor `services/agent-gateway/openapi.json` as `contracts/openapi/agent-gateway.yaml`).
- [ ] Coordinate with ZeSporteXte owners on `@njz/vaultbrain-events`, `@njz/agent-protocol`, `@njz/auth-types` package shape.
- [ ] First sprint plan in `.agents/session-workplans/SW-20260525-phase1-bootstrap.md`.

## Lessons learned

- Mirroring upstream framework conventions exactly is faster than designing from scratch — and pays back in agent portability.
- The Build Plan's "$0 budget" constraint is achievable but requires diligence about content licensing and asset pipelines.
- Two-app split (Next.js + Vite) is the right shape but adds CI complexity to manage early; worth it.

## References

- ADR-0001..0006 (this PR)
- Uploaded source: `3NJZOS_PRD.docx`, `3NJZOS_Build_Plan.docx`, `3NJZOS_Market_Review.docx`
- Upstream framework reference: `notbleaux/ZeSporteXte` `.agents/`, `ROOT_AXIOMS/`, `.doc-tiers.json`
- Legacy preserved at: `legacy/satire-deck-veritas` branch
