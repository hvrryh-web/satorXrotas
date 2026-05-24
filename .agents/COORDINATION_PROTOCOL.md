[Ver001.000]

# COORDINATION_PROTOCOL — NJZ RAT-OS

How multiple AI agents (and the humans driving them) coordinate without stepping on each other.

## Mental Model

Think of the repo as a *shared workspace with channels*, not a queue. At any moment several agents may be active. Each agent must:

1. Declare what it's about to do (in a session workplan).
2. Pick a single channel/lane and stay in it.
3. Surface its decisions where the next agent can find them.
4. Not modify another agent's open work without coordination.

## Channels

A channel is a logical lane of work. Every PR belongs to exactly one channel. Channels are listed in `.agents/channels/index.json`.

Default channels:

| Channel | Lane | Owner-of-record |
|---------|------|-----------------|
| `framework` | `.agents/`, `ROOT_AXIOMS/`, `.doc-*.json` | Coordinator agent |
| `product-docs` | `docs/product/` | Architect agent |
| `architecture` | `docs/architecture/`, `ARCHITECTURE.md` | Architect agent |
| `web-app` | `apps/web/` | Implementer agent |
| `site` | `apps/site/` | Implementer agent |
| `packages-ui` | `packages/@njz-os/ui/` | Designer agent |
| `packages-engines` | `packages/@njz-os/{focus,audio,polyworld,...}-engine/` | Implementer agent |
| `adapters` | `packages/adapters/`, `contracts/` | Data-engineer agent |
| `infra` | `infra/`, `.github/workflows/`, `services/rat-os-api/` | Platform agent |
| `tests` | `tests/`, `packages/*/**/test/` | Critic agent |
| `dev-reports` | `docs/dev-reports/` | Coordinator agent |

## Session Lifecycle

1. **Start.** Read T0 docs. Pick a channel. Drop a workplan in `.agents/session/<branch>-<timestamp>.md` (template at `docs/ai-operations/SESSION_WORKPLAN_TEMPLATE.md`).
2. **Work.** Stay in your channel. If you discover work in another channel, file an issue rather than expanding scope.
3. **Decide.** Every substantive choice → one line in `.agents/DECISION_LOG.md`. Big choices → ADR.
4. **Hand off.** If your task spans multiple sessions, drop a handoff doc in `.agents/handoff/`.
5. **Close.** Commit, push, open PR. Tag the channel in PR title: `[web-app] add focus hero stub route`.

## Conflict Resolution

| Conflict | Resolution |
|----------|-----------|
| Two agents want to edit the same file | First-to-PR wins; second rebases |
| Two agents disagree on a design choice | Open competing ADRs; CODEOWNER decides |
| An agent crosses channels mid-PR | Reviewer requests split |
| An agent skips the workplan step | Reviewer requests retroactive workplan before approval |

## Inter-Agent Communication

- **Synchronous:** through the user (the human in the loop).
- **Asynchronous:** through `.agents/handoff/<topic>.md` files. A handoff is small (< 200 lines), focused on one topic, dated, and self-contained.
- **Broadcast:** through `.agents/PROJECT_STATUS_OVERVIEW.md` (the dashboard).

## Skill-Map Lookup

Before you do something specialised (e.g. write a Three.js shader, build a binaural beat synth, design a state machine), check `.agents/SKILL_MAP.md`. If another agent is the registered owner of that skill, ask the user whether to defer.

## Escalation

If a contract violation, gate violation, or hard-rule violation is requested, refuse and surface the conflict via `docs/ai-operations/ESCALATION_PROTOCOL.md`. The user can override but must acknowledge the violation explicitly.
