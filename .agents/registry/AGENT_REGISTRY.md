[Ver001.000]

# AGENT_REGISTRY — NJZ RAT-OS

Live list of agents authorized to work in this repository. Maintained by the Coordinator role.

| Agent ID | Tool / Model | Role(s) | Authorized channels | Notes |
|----------|--------------|---------|---------------------|-------|
| `claude-opus-4.7` | Claude Code | Coordinator (primary), Architect | all | Bootstrap agent |

## Onboarding

To onboard a new agent:

1. Open a PR adding a row to this table.
2. Assign one primary role and at most two secondary roles.
3. List authorized channels (from `.agents/COORDINATION_PROTOCOL.md`).
4. CODEOWNER approval required.

## Off-boarding

To off-board, simply remove the row and append a one-liner to `.agents/DECISION_LOG.md`.
