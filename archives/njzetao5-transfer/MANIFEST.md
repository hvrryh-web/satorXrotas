# Archive Manifest: NJZetao5 Transfer

**Transfer Date:** 2026-05-11
**Source Repository:** [notbleaux/NJZetao5](https://github.com/notbleaux/NJZetao5)
**Source Commit:** `7705d855af4beece81ecbef464f72ffb1b25eb1e` (main)
**Destination Path:** `archives/njzetao5-transfer/`
**Transfer Type:** Provenance-preserving archive import (file copy, not git history merge)

---

## Why this transfer happened

`notbleaux/NJZetao5` previously carried two conflicting identities:

1. **Archive role** — preservation of legacy ZeSporteXte / eSports-EXE governance and
   migration material (the role described in its original GitHub description:
   *"Archived governance and documentation files for notbleaux/eSports-EXE"*).
2. **Platform-foundation blueprint** — an active, forward-looking design for a
   multi-agent webapp platform under the PixelOffice working name, with product
   scope, repo-structure proposals, implementation backlog, and MVP API/UI templates.

A repository review determined the two identities were incompatible inside a
single repo. The decision was:

- `notbleaux/NJZetao5` becomes the **active PixelOffice Wiki & Governance
  Repository** (governance folders, ADRs, PRDs, CRITs, prompts, standards,
  roadmap, release gates).
- The historical archive material — including the platform-foundation blueprint
  drafts and the legacy Godot game migration tree — moves here, to
  `hvrryh-web/satorXrotas`, which already hosts the related Tact FPS Simulation
  Game project and its own `pre-historic-legacy/` archive area.

This manifest preserves provenance so the original organization, file paths,
and intent remain readable after the move.

---

## Relationship to PixelOffice / ZeSporteXte / satorXrotas

| Project / repo | Role after this transfer |
|---|---|
| `notbleaux/NJZetao5` | Active PixelOffice **Wiki & Governance** repo. |
| `hvrryh-web/satorXrotas` | Tact FPS Simulation Game (active) + archive host. |
| `archives/njzetao5-transfer/` (this folder) | Frozen snapshot of pre-pivot NJZetao5 content. |
| `pre-historic-legacy/` (this repo, separate folder) | Pre-existing satorXrotas archive — **not modified by this transfer**. |

The platform-foundation drafts captured here describe an early conception of
the PixelOffice multi-agent platform. They are retained for reference; current
PixelOffice governance, standards, and roadmap live in
`notbleaux/NJZetao5` going forward.

---

## Contents

All paths below are relative to `archives/njzetao5-transfer/` in this repo.
Original paths refer to `notbleaux/NJZetao5` at the source commit above.

### `platform-foundation/`
**Original path:** `platform-foundation/`
**Status:** ARCHIVE — superseded by the new Wiki & Governance structure in NJZetao5.

Documents:

- `README.md` — Platform-foundation overview (old PixelOffice blueprint).
- `PRODUCT_SCOPE.md` — Product scope draft for the multi-agent webapp.
- `ROADMAP.md` — Roadmap for the platform build-out.
- `REPO_STRUCTURE.md` — Proposed monorepo / package layout for the platform.
- `IMPLEMENTATION_BACKLOG.md` — Backlog converted from earlier planning notes.
- `ENGINEERING_STANDARDS.md` — Engineering standards proposal.
- `ONBOARDING.md` — Contributor onboarding draft.
- `QUICKSTART.md` — Quickstart draft for the unbuilt platform.
- `PIXELOFFICE_AGENT.md` — Notes on the PixelOffice agent concept.
- `WIKI_OPERATIONS_PROTOCOL.md` — Wiki operations protocol draft (carried
  forward in updated form into the new NJZetao5 governance tree).
- `AI_DEVELOPER_CLOUD_SERVICES_PLAYBOOK.md` — Cloud services playbook draft.
- `CODEBASE_RESEARCH_AND_SERVICE_EXAMPLES.md` — Research notes on reference codebases.
- `REVIEW_SUITE_RECOMMENDATIONS.md` — Review-tooling recommendations.
- `templates/` — Original MVP API contract, service contract template,
  interface acceptance checklist, and `.env.example`.

### `godot-game-migration/`
**Original path:** `godot-game-migration/`
**Status:** ARCHIVE — legacy game migration assets from the 2026-03-30 snapshot.
Related to but distinct from `pre-historic-legacy/01-simulation-game/` already
present in this repo. Review for overlap before reuse.

Top-level contents:

- `2026-03-30/MIGRATION_LOG.md` — Migration log for that snapshot.
- `2026-03-30/radiantx-game/` — RadiantX live-season module and tests.
- `2026-03-30/simulation-game/` — Simulation game source: `Defs/`, `scenes/`,
  `scripts/`, `entities/`, `addons/`, `maps/`, plus `project.godot` and
  `INTEGRATION_UPDATE.md`.

### `ORIGINAL-README.md`
**Original path:** `README.md` (root)
**Status:** ARCHIVE — the pre-pivot README describing NJZetao5 as the "core
webapp repository for a multi-agent collaboration ecosystem." Preserved so
the original framing is not lost; the active NJZetao5 README is being rewritten
to describe the Wiki & Governance role.

---

## What was deliberately NOT moved

- `.gitattributes`, `.gitignore` — repo-local hygiene files; not part of the
  archive material.
- `.git/` history — this is a file-level archive copy, not a history-rewrite
  merge. Use the source commit hash above to inspect history in
  `notbleaux/NJZetao5` if needed.

## What was NOT modified in this repo

This transfer adds files only under `archives/njzetao5-transfer/`. It does not
touch `pre-historic-legacy/`, `active/`, `frameworks/`, `roles/`, `tools/`,
`context/`, `docs/`, or the existing satorXrotas Tact FPS Simulation Game
identity in any way.
