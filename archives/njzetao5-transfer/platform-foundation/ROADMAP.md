# Phased Delivery Milestones

## Phase 1: Foundation
- Finalize scope, standards, and scaffold
- Set CI baseline and release policy

### Acceptance Criteria
- Domain structure adopted
- CI gates active for PRs
- Quickstart works on clean machine

## Phase 2: MVP Simulation Platform
- WebApp planner + sprite assistant MVP
- Core API and task lifecycle

### Acceptance Criteria
- Users can create/manage projects and tasks
- Sprite responds to planner events
- Basic simulation metrics visible

## Phase 3: AI Integrations
- Provider adapters and tool-call audit trail
- Guardrails and action confirmation UX

### Acceptance Criteria
- AI actions are attributable and reviewable
- Failed calls have fallback and visible errors
- Security checks pass for AI integration paths

## Phase 4: Browser Extension
- Capture context from browser and submit to planner
- Sync with active project workspace

### Acceptance Criteria
- Context capture saves into selected project
- Extension auth/session handling is stable
- End-to-end extension-to-app flow tested

## Phase 5: Scale and Operations
- Performance hardening, observability, and cost controls
- Multi-team workflows and RBAC improvements

### Acceptance Criteria
- SLO dashboards and alerts in place
- Load tests meet target thresholds
- Role-based access controls verified
