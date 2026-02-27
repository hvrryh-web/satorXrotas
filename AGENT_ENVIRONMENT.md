# Kimi/Claude/Copilot Agent Environment

This workspace is configured for:
- GitHub Copilot (see .github/copilot-instructions.md)
- Claude (see CLAUDE.md)
- Kimi (Moonshit AI) with skills in .agents/skills/

## Usage
- All agents must read their respective instruction files before making changes.
- Skills for Kimi are in .agents/skills/ (see each SKILL.md for usage).
- Copilot and Claude follow structured task format (see copilot-instructions.md, CLAUDE.md).

## VS Code
- Workspace settings in .vscode/settings.json ensure correct formatting and agent integration.
- Python, TypeScript, GDScript, and Markdown settings are pre-configured.

## Agent Skills
- Kimi: .agents/skills/*/SKILL.md
- Claude: CLAUDE.md
- Copilot: .github/copilot-instructions.md

## For new skills or agent integrations:
- Add new skills to .agents/skills/ and document in SKILL.md
- Update this file and settings.json if new config paths are needed.
