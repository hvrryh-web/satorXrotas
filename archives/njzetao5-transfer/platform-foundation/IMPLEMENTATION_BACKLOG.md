# API + Interface Implementation Backlog (Execution-Ready)

This backlog converts the research guidance into concrete delivery items with exact target files, endpoint contracts, UI primitives, and phase gates.

## Track 1: API Tooling Enhancements (Priority)

### A1. MVP contract baseline
- **Contract file:** `platform-foundation/templates/mvp-api-contract.yaml`
- **Endpoint groups:**
  - Project/task lifecycle
    - `POST /v1/projects`
    - `POST /v1/projects/{projectId}/tasks`
    - `PATCH /v1/tasks/{taskId}/status`
  - Agent actions and approvals
    - `POST /v1/agent-actions`
    - `POST /v1/agent-actions/{actionId}/approvals`
  - Context sync
    - `POST /v1/context-sync/jobs`
    - `GET /v1/context-sync/jobs/{jobId}`
  - Operations/telemetry
    - `GET /healthz`
    - `GET /readyz`

### A2. Validation + typed DTO layer
- **Required DTOs (contract-first):**
  - `CreateProjectRequest`, `CreateTaskRequest`, `UpdateTaskStatusRequest`
  - `CreateAgentActionRequest`, `AgentActionApprovalRequest`
  - `CreateContextSyncJobRequest`
- **Boundary checks:** required fields, enum constraints, transition constraints, and policy inputs.

### A3. Shared middleware and controls
- Correlation ID middleware (`x-correlation-id`) on all requests.
- Structured audit events for agent actions and approvals.
- Explicit policy guard for high-impact actions before execution.

### A4. Reliability + idempotency
- Require `Idempotency-Key` for context sync and async action creation routes.
- Return stable `202` responses for accepted async operations.
- Persist retry-safe operation identity by idempotency key.

### A5. Telemetry baseline
- Logs: request lifecycle + action audit payload.
- Traces: route span + downstream operation span linkage by correlation ID.
- Metrics: request duration/count/error and async queue outcome counts.

## Track 2: Interface Design + Functionality Enhancements

### B1. UI state primitives
- **Canonical states:** planner status, risk status, approval-required status.
- **Target artifact:** `platform-foundation/templates/interface-acceptance-checklist.md`

### B2. Sprite integration
- Planner/risk signal mapping:
  - `task_assigned -> advising`
  - `risk_spike -> warning`
  - `milestone_hit -> celebrating`
  - fallback -> `idle`

### B3. Confirmation/fallback/audit UX
- High-impact action confirmation flow before submit.
- Clear failure fallback with recovery action (retry/cancel/escalate).
- User-visible audit trace entries for autonomous actions.

### B4. Accessibility acceptance
- Keyboard navigation for planner and action confirmation controls.
- Focus transitions on modal open/close and error states.
- Status messaging for success, in-progress, failure, and approval-required states.

### B5. UX observability
- Emit interaction events for assignment, approval, completion, and error.
- Correlate UI events to API correlation ID when available.

## Delivery Sequence (Phased)

### Phase A
- Contract baseline + DTO/validation scope + middleware policy.

### Phase B
- Approval flow + audit visibility in UI.

### Phase C
- Context sync orchestration + idempotency/retry hardening.

### Phase D
- Sprite polish + accessibility/performance pass.

## Definition of Done (per increment)
- Contract section exists and is testable.
- Security checks are present at boundaries (validation + policy).
- Observable behavior is present (log/trace/metric hooks).
- User-facing failure/recovery behavior is explicit.
- Mapped to roadmap acceptance criteria before merge.
