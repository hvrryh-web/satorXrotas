# Startup & Quickstart Foundations

## 1) Local Development Setup
1. Install required toolchains:
   - Node.js LTS (WebApp, Website, Extension)
   - .NET 8 SDK (simulation and existing C# modules in this repository)
   - Godot 4.x CLI/editor (simulation scenes and GDScript tests)
   - Git + Git LFS
2. Copy environment template:
   - `platform-foundation/templates/.env.example` -> `.env.local`
3. Start service dependencies and run app modules in parallel.

## 2) Environment Template Policy
- Keep all required keys in `.env.example`.
- Use provider-specific secrets only in local secure stores or CI secrets.
- Add validation on startup for missing required vars.

## 3) Service Contract Policy
- All service endpoints documented via versioned contracts.
- Contract changes require changelog entry and migration note.
- Use `platform-foundation/templates/service-contract-template.yaml` for new endpoints.
- Use `platform-foundation/templates/mvp-api-contract.yaml` as the baseline MVP contract seed.

## 4) Interface Readiness and Acceptance
- Use `platform-foundation/templates/interface-acceptance-checklist.md` for planner/sprite UX acceptance in Phases B-D.
- Require keyboard, focus, status messaging, and observability checks before UI merge.

## 5) Startup Readiness Checklist

- Scaffold structure created and committed
- CI checks running on pull requests
- Baseline auth and project service endpoints available
- Onboarding docs complete and tested by a new contributor
