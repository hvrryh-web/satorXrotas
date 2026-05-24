# Changelog

All notable changes to NJZ RAT-OS are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Added — Phase 0 Bootstrap

- Canonical AI-orchestration framework (NJZPOF v0.2): `.agents/`, `ROOT_AXIOMS/`, `.doc-tiers.json`, `.doc-registry.json`.
- Refined product documentation: PRD, OKRs, market review, personas, pricing, roadmap.
- ADR-0001 through ADR-0006 covering monorepo structure, package consumption, state backend, app split, polyworld renderer, audio engine.
- Prototype-system specs PS-001 through PS-007 (one per module).
- Dev report DR-0001 documenting Phase 0 bootstrap decisions.
- pnpm + Turborepo monorepo skeleton with apps (`site`, `web`), packages (`@njz-os/*`, `adapters/*`, `config/*`), services scaffold (`rat-os-api`), contracts (OpenAPI + events), infra stubs.
- CI workflow (lint + typecheck + tests + doc-tier validation).

### Preserved

- Previous repository contents (Satire-deck-Veritas restructure, pre-historic-legacy, frameworks, etc.) preserved on branch `legacy/satire-deck-veritas` — recoverable indefinitely.
