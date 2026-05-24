[Ver001.000]

# COLLABORATION_RUNBOOK — NJZ RAT-OS

Concrete playbook for the most common multi-agent workflows in this repo. Each runbook is a numbered sequence; copy + adapt.

## Runbook 1 — Bootstrap a New Module Package

When: a new `@njz-os/<name>` package needs to exist.

Channel: `packages-engines` (or `packages-ui` for visual primitives).

```
1. Architect agent: open ADR in docs/architecture/ADR/ proposing the module
   surface, dependencies, and gate (`G1.<name>` or `G2.<name>`).
2. CODEOWNER review → ADR Status: Accepted.
3. Implementer agent: pnpm module:new <name>
4. Fill packages/@njz-os/<name>/{package.json, tsconfig.json, src/index.ts, README.md}.
5. Add the module spec at docs/prototype-systems/PS-XXX-<name>.md.
6. Register the package's domain types in .agents/SCHEMA_REGISTRY.md.
7. Open PR with title [packages-engines] add @njz-os/<name>.
```

## Runbook 2 — Add a New ADR

When: a non-trivial architecture decision needs to be recorded.

Channel: `architecture`.

```
1. pnpm adr:new "Short title"
2. Edit docs/architecture/ADR/ADR-XXXX-<slug>.md filling in
   Context / Decision / Consequences / Alternatives Considered.
3. Status: Proposed.
4. Open PR with title [architecture] ADR-XXXX <title>.
5. On approval: flip Status: Accepted in a follow-up commit.
6. Append one line to .agents/DECISION_LOG.md referencing the ADR.
```

## Runbook 3 — Add or Update a Service Contract

When: RAT-OS needs a new endpoint or event from ZeSporteXte.

Channel: `adapters`.

```
1. Confirm the upstream endpoint exists in notbleaux/ZeSporteXte
   (read services/api or services/vaultbrain). If not, file an issue there
   first and pause this PR.
2. Update contracts/openapi/njz-rat-os.yaml (or contracts/events/*.json).
3. Regenerate the typed client: pnpm --filter @njz-os/adapters-api-client generate.
4. Update packages/adapters/<service>-client/ to expose the new method.
5. Open PR with title [adapters] expose <feature> from <service>.
6. Smoke-test against staging if Phase 0 done.
```

## Runbook 4 — Open a Phase Gate

When: a gate listed in `.agents/PHASE_GATES.md` is ready to flip.

Channel: `framework`.

```
1. Verify all unlock criteria in PHASE_GATES.md are met (link evidence).
2. Get CODEOWNER signoff in PR review.
3. Edit PHASE_GATES.md: flip LOCKED → OPEN with date.
4. Append a row to .agents/DECISION_LOG.md.
5. If gate opening involves new architecture, add an ADR.
6. Open PR with title [framework] open gate G<N>.<name>.
```

## Runbook 5 — Cross-Channel Refactor

When: a change touches multiple channels (e.g. renaming a domain type used in core + adapters + apps).

```
1. Architect agent: write the refactor plan as a session workplan in
   .agents/session-workplans/SW-<date>-<slug>.md.
2. Cross-link from .agents/active/.
3. Implementer agent: open ONE PR that touches all affected channels.
   Do NOT split a coupled refactor across PRs.
4. Reviewer flags any non-mechanical changes as scope creep.
5. On merge: log to DECISION_LOG.md if the refactor changed any contract.
```

## Runbook 6 — Recover Legacy Content

When: you need something that was deleted in the RAT-OS bootstrap.

```
1. Find the file on legacy/satire-deck-veritas branch:
   git show legacy/satire-deck-veritas:path/to/file
2. Decide whether it belongs in the new structure (most pre-historic-legacy
   content does NOT — it predates the RAT-OS thesis).
3. If yes: cherry-pick or copy into the appropriate channel, attribute the
   origin in a code comment or doc footer.
4. Never re-merge legacy/* into main wholesale.
```

## Runbook 7 — Session Handoff

When: you're closing a session mid-task.

```
1. Push your branch (do not merge).
2. Drop .agents/handoff/<topic>-<date>.md describing:
   - what's done
   - what's next
   - any blockers / open questions
   - relevant file paths and line numbers
3. Update .agents/active/<branch>.md if it exists.
4. The next agent reads handoff + workplan before touching anything.
```
