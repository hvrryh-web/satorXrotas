[Ver001.000]

# Session Lifecycle — NJZ RAT-OS

How any AI agent starts, runs, and closes a session in this repo.

## 1. Start

Read in this order:

1. `CLAUDE.md` (or `AGENTS.md` for non-Claude tools)
2. `MASTER_PLAN.md`
3. `.agents/AGENT_CONTRACT.md`
4. `.agents/PHASE_GATES.md`
5. `.agents/SCHEMA_REGISTRY.md` (skim)
6. `.agents/PROJECT_STATUS_OVERVIEW.md`

Optional: skim `.doc-registry.json` so you know where to look for any topic.

## 2. Triage

- Identify the channel from `.agents/COORDINATION_PROTOCOL.md` that matches your task.
- Verify the relevant `PHASE_GATE` is OPEN. If not, refuse the work and explain.
- Check `.agents/active/` and `.agents/handoff/` for in-flight work on the same channel — coordinate before stepping on it.

## 3. Plan

For any task spanning more than a single tool call, drop a session workplan in `.agents/session/<branch>-<timestamp>.md` using `SESSION_WORKPLAN_TEMPLATE.md`. The workplan answers:

- What channel?
- What's the smallest end-to-end deliverable?
- What's explicitly out of scope?
- What's the verification step?

## 4. Work

- Stay in your channel.
- Edit existing files in preference to creating new ones.
- Follow the code/doc standards in `ROOT_AXIOMS/02_STANDARDS/`.
- If a substantive decision arises, append to `.agents/DECISION_LOG.md`; open an ADR if non-trivial.

## 5. Verify

Before commit:

```bash
pnpm typecheck
pnpm lint
pnpm test --filter <affected>
pnpm doc-tier:check
```

Pre-commit hooks will rerun these subsetted to staged files; don't bypass.

## 6. Commit

Conventional commits format. Scope = channel. Example:

```
feat(focus-engine): add pomodoro state machine

Implements the 25/5 pomodoro cycle per ADR-0007.
Adds tests for state transitions and timer drift tolerance.

Refs ADR-0007.
```

## 7. Push + PR

- Push to your feature/agent branch.
- Open PR with title `[<channel>] <description>`.
- Body: Why (not just What). Link ADRs, PS specs, DRs.

## 8. Close session

- Append a one-liner to `.agents/DECISION_LOG.md` if you made a decision.
- If the work spans more sessions, drop a handoff file in `.agents/handoff/`.
- Update `.agents/active/<branch>.md` if you opened/closed an in-flight workstream.
- Update `.agents/PROJECT_STATUS_OVERVIEW.md` if the change moves the dashboard.

## Failure Modes

| Symptom | Action |
|---------|--------|
| Pre-commit hook fails | Fix the cause; don't bypass |
| Typecheck fails on an unrelated file | Surface to the user; do not "fix" by editing unrelated code |
| You discover a contract violation in your branch | Refuse to commit; open an issue; surface to user |
| You discover a contract violation already on `main` | Surface; open a fix PR; reference DECISION_LOG |
| Vaultbrain / upstream service unreachable in tests | Use mocks; don't disable the test |
