# Runbooks

Step-by-step procedures for operational tasks. Each runbook is small, focused, and stays current.

## Index

| Runbook | When |
|---------|------|
| `incident-response.md` | Production incident (Phase 1+) |
| `rollback.md` | Vercel / Render deployment rollback |
| `secret-rotation.md` | Rotate vaultbrain shared secret, agent gateway API key, etc. |
| `upstream-bump.md` | Bump `@njz/*` package versions |

(Empty until Phase 1 — runbooks added as needs surface.)

## Format

Each runbook:

1. **When to use** — concrete triggers.
2. **Preconditions** — what must be true.
3. **Steps** — numbered, copy-pasteable commands.
4. **Verification** — how to know it worked.
5. **Rollback** — what to do if it didn't.
6. **Postconditions** — what should now be true.
