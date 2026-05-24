# tools/

Small Node scripts invoked via root `package.json` aliases. Pure JS (`.mjs`) — no build step.

| Tool | Invoked via | Purpose |
|------|-------------|---------|
| `doc-tier-check/` | `pnpm doc-tier:check` | Validate `.doc-tiers.json` + root `.md` manifest |
| `adr-new/` | `pnpm adr:new "<title>"` | Scaffold a new ADR file |
| `module-new/` | `pnpm module:new "<name>"` | Scaffold a new `@njz-os/<name>` package |

Agents call these via `Bash`; humans via `pnpm`.
