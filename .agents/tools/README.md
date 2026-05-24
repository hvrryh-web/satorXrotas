# .agents/tools/

Agent-callable tools — small scripts, MCP entry points, generators that agents invoke during a session.

Names mirror the `tools/` directory at the repo root for tools that have a CLI counterpart. Files here document *how an agent calls them*, not how a human runs them.

Examples (to be filled):

- `doc-tier-check.md` — when and how to invoke the tier validator
- `adr-new.md` — wrapping `pnpm adr:new`
- `module-new.md` — wrapping `pnpm module:new`
