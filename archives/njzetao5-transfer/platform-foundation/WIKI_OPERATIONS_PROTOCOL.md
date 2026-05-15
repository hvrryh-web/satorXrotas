# Wiki: Operations, Tooling, and Agent Learning Protocol

This document is a wiki-ready operating brief for the NJZetao5 repository/platform.
It consolidates stack awareness, networking/tooling needs, identified gaps, and actionable protocols for future implementation.

## 1) Tech Stack Inventory (Current + Intended)

### Current in-repo reality
- Strategy and planning docs for product scope, standards, onboarding, and roadmap.
- Legacy simulation/game migration assets including .NET 8 solution artifacts.

### Intended product stack (from platform goals)
- **Web app and website surfaces:** Node.js ecosystem frontends.
- **Service/API layer:** centralized backend services for auth, project state, and orchestration.
- **Agent orchestration layer:** MCP/ACP-compatible coordination and tool invocation governance.
- **Knowledge layer:** collaborative RAG + second-brain context indexing and retrieval.
- **UX layer:** sprite-driven visual assistant model for project interaction.

## 2) Networking and Environment Needs

- Centralized environment model for agent and user traffic.
- Service-to-service contracts for planner, agent adapter, logging, and knowledge services.
- Secure secret handling and environment validation before runtime.
- Audit-capable logs for agent actions and human approvals.
- Future-ready observability paths: metrics, traces, and health/SLO dashboards.

## 3) Team Tooling Needs and Gaps

### Immediate needs
- Unified implementation repository structure from `platform-foundation/scaffold`.
- CI pipelines for static checks, builds, tests, and vulnerability scanning.
- Baseline API contract lifecycle (versioning + migration notes).
- Shared workflow for context capture from chat/tool activity into team knowledge.

### Gaps to close next
- Production-ready MCP/ACP adapter implementation.
- Formal persona library schema (roles, permissions, scenarios, conditions).
- Retrieval/indexing pipeline standards for second-brain context assets.
- Scheduling/automation for recurring review cycles and log polling.

## 4) AI Lead-Agent Operating Protocol (Claude, Kimi, DeepSeek)

1. **Contribution channel**
   - Sub-agents append structured proposals/findings into the shared weekly log.
2. **Weekly polling cadence**
   - Lead agents poll and review every Sunday.
3. **Triage rubric**
   - Classify submissions into: immediate execution, prototype queue, research backlog, or reject.
4. **Knowledge ingestion**
   - Accepted items are normalized into second-brain entries with tags, source links, and confidence notes.
5. **Decision traceability**
   - Each accepted/rejected item gets a short decision record for future context and accountability.

## 5) Second-Brain Library Protocol

- Use keyed identifiers per topic/project/initiative.
- Require metadata: source, owner, timestamp, status, confidence, and dependencies.
- Maintain both:
  - human-readable summary layer
  - retrieval-oriented chunk/vector layer
- Keep bidirectional links between long-form notes and executable tasks.
- Enforce archival policy for stale context instead of silent deletion.

## 6) Implementation Backlog (Actionable)

- Define a canonical schema for log entries and proposal records.
- Stand up a minimal MCP/ACP adapter service contract.
- Build ingestion pipeline for Notion/Obsidian/Hermes exports into indexed context storage.
- Add role-based access model for agent permissions and approvals.
- Add dashboard for weekly polling outcomes, adoption metrics, and backlog health.

## 7) Repository Wiki Population Guidance

If mirrored to a GitHub Wiki, use this page set first:
- Home: Mission, scope, and current status
- Architecture: stack, domains, and network model
- Agent Protocols: lead/sub-agent operating rules
- Knowledge Ops: second-brain lifecycle and indexing standards
- Integrations: Notion/Obsidian/Hermes and external tool contracts
- Security & Governance: auth, audit, approvals, and incident workflow

This file is the starting point for long-term memory and operating standards and should be updated as implementation decisions become concrete.

## 8) Seeded Wiki Expansion Pack

- `AI_DEVELOPER_CLOUD_SERVICES_PLAYBOOK.md` defines developer/cloud/AI service patterns and autonomy rules.
- `REVIEW_SUITE_RECOMMENDATIONS.md` provides OKR/CRIT/PRD/ARD + sprint/roadmap and gap-driven recommendations.
- Re-run and refresh these pages at each sprint boundary to keep the wiki aligned with execution reality.
