# Codebase Research and Service Example Pack

This document captures strong implementation patterns from widely respected web codebases and adapts them for NJZetao5 project services.

## 1) Research Scope and Selection Rules

### Selection criteria
- Publicly inspectable code or official engineering guidance.
- Demonstrated quality in performance, accessibility, and maintainability.
- Patterns portable to multi-agent orchestration and second-brain workflows.

### Candidate set reviewed
- **Next.js production guidance** (routing, rendering, caching, runtime boundaries)
- **Node.js operational patterns** (runtime reliability and process controls)
- **OpenTelemetry** (trace propagation and telemetry contracts)
- **OWASP API Security Top 10** (secure-by-default API and tool-call controls)
- **Well-regarded OSS web codebases**: freeCodeCamp, Ghost, Excalidraw, and Bulletproof React architecture conventions

## 2) Best-Pattern Extraction Summary

### A) Performance patterns
- Cache-aware rendering (SSG/ISR/SSR mix by route criticality).
- Payload and bundle discipline (split by route/feature and defer non-critical assets).
- Event processing idempotency for replay-safe retries.

### B) Accessibility and UX quality
- Semantic-first UI components with keyboard-first navigation.
- Shared component primitives with predictable state and focus behavior.
- Built-in a11y checks in feature acceptance criteria.

### C) Reliability and operations
- Health/readiness endpoints and graceful shutdown handling.
- Structured logs with request IDs and actor/tool metadata.
- Trace/metric/error correlation across API and worker workflows.

### D) Security and governance
- Input schema validation at every boundary.
- Least-privilege tokens for tool/agent operations.
- Immutable audit trails for high-impact actions.

## 3) Porting Matrix (What to Adapt for NJZetao5)

| Source Pattern | Port Target in NJZetao5 | Adaptation Goal |
| --- | --- | --- |
| Feature-sliced React/TypeScript structure | WebApp planner and sprite UI | Faster onboarding + maintainable growth |
| Request/trace correlation middleware | AI interaction layer and APIs | Explainable action lineage |
| Event idempotency keys | Planner lifecycle and context sync jobs | Safe retries and duplicate suppression |
| Policy guardrails for risky actions | Agent action execution path | Controlled autonomy with human checkpoints |
| Background ingest + indexing workers | Second-brain context pipeline | Reliable context refresh and retrieval quality |

## 4) Acceptable Code Range Framework (Taste + Completion + Outcomes)

### Tier A (preferred)
- Clear domain boundaries, strict typing, explicit error paths.
- Observable by default (logs + traces + metrics).
- Security controls integrated into normal flow.

### Tier B (acceptable short-term)
- Correct behavior and tests present, but observability/security still partial.
- Allowed only with documented follow-up tasks and sprint assignment.

### Tier C (reject)
- Hidden side effects, no auditability, or unsafe default permissions.
- Missing failure handling for external calls.

## 5) Explicit Service/Feature Code Examples

> The following examples are implementation-ready templates aligned to the project plans (planner lifecycle, audit trail, approvals, second-brain sync, scoring, and sprite behavior mapping).

### 5.1 Planner task lifecycle service (TypeScript)
```ts
export type TaskStatus = 'todo' | 'in_progress' | 'blocked' | 'done';

interface TaskEvent {
  taskId: string;
  from: TaskStatus;
  to: TaskStatus;
  actorId: string;
  correlationId: string;
  occurredAt: string;
}

const allowedTransitions: Record<TaskStatus, TaskStatus[]> = {
  todo: ['in_progress', 'blocked'],
  in_progress: ['blocked', 'done'],
  blocked: ['todo', 'in_progress'],
  done: []
};

export function transitionTaskStatus(current: TaskStatus, next: TaskStatus): void {
  if (!allowedTransitions[current].includes(next)) {
    throw new Error(`Invalid transition: ${current} -> ${next}`);
  }
}

export function buildTaskEvent(input: Omit<TaskEvent, 'occurredAt'>): TaskEvent {
  return { ...input, occurredAt: new Date().toISOString() };
}
```

### 5.2 Tool-call audit middleware (Node API)
```ts
import { randomUUID } from 'node:crypto';
import type { NextFunction, Request, Response } from 'express';

interface AgentRequest extends Request {
  correlationId?: string;
  user?: { id?: string };
}

export function auditMiddleware(req: AgentRequest, res: Response, next: NextFunction): void {
  const incoming = req.headers['x-correlation-id'];
  const correlationId = (Array.isArray(incoming) ? incoming[0] : incoming) || randomUUID();
  const auditedReq = req as AgentRequest & { correlationId: string };
  auditedReq.correlationId = correlationId;
  const startedAt = Date.now();

  res.on('finish', () => {
    const payload = {
      correlationId,
      actorId: auditedReq.user?.id ?? 'anonymous',
      route: auditedReq.originalUrl,
      method: auditedReq.method,
      statusCode: res.statusCode,
      durationMs: Date.now() - startedAt
    };
    console.log(JSON.stringify({ event: 'tool_call_audit', ...payload }));
  });

  next();
}
```

### 5.3 Approval guard for high-impact agent actions
```ts
const highRiskActions = new Set(['delete_project', 'bulk_reassign', 'publish_decision_log']);

export function requireApproval(actionName: string, isApproved: boolean): void {
  if (highRiskActions.has(actionName) && !isApproved) {
    throw new Error(`Approval required for action: ${actionName}`);
  }
}
```

### 5.4 One-click context sync workflow (second brain)
```ts
interface ContextSource {
  name: 'notion' | 'obsidian' | 'hermes';
  pullUpdates: (cursor?: string) => Promise<{ cursor: string; docs: ContextDocument[] }>;
}

interface ContextDocument {
  id: string; // Stable source-specific identifier (e.g., SHA-256 of canonical source path + title).
  sourcePath?: string;
  updatedAt: string;
  content: string | { text: string; metadata?: Record<string, unknown> };
}

/** Removes duplicates by `id` and keeps the newest `updatedAt` document for that id. */
declare function dedupeByStableKey(docs: ContextDocument[]): ContextDocument[];
/** Persists source documents before indexing for provenance and replay-safe recovery. */
declare function persistRawContext(source: ContextSource['name'], docs: ContextDocument[]): Promise<void>;
/** Queues normalized documents for chunking/vector indexing workers. */
declare function enqueueIndexingJobs(source: ContextSource['name'], docs: ContextDocument[]): Promise<void>;

export async function runContextSync(sources: ContextSource[]) {
  for (const source of sources) {
    const { docs } = await source.pullUpdates();
    const uniqueDocs = dedupeByStableKey(docs);
    await persistRawContext(source.name, uniqueDocs);
    await enqueueIndexingJobs(source.name, uniqueDocs);
  }
}
```

### 5.5 Proposal scoring service (impact/risk/confidence)
```ts
interface ProposalScoreInput {
  impact: number;      // 1..5
  complexity: number;  // 1..5
  risk: number;        // 1..5
  confidence: number;  // 1..5
}

export function scoreProposal(input: ProposalScoreInput): number {
  const weighted =
    input.impact * 0.4 +
    (6 - input.complexity) * 0.2 +
    (6 - input.risk) * 0.2 +
    input.confidence * 0.2;

  return Number(weighted.toFixed(2));
}
```

### 5.6 Sprite state mapping from planner events
```ts
type SpriteState = 'idle' | 'advising' | 'warning' | 'celebrating';

type PlannerSignal = 'task_assigned' | 'risk_spike' | 'milestone_hit' | 'no_event';

export function mapSignalToSpriteState(signal: PlannerSignal): SpriteState {
  switch (signal) {
    case 'task_assigned':
      return 'advising';
    case 'risk_spike':
      return 'warning';
    case 'milestone_hit':
      return 'celebrating';
    default:
      return 'idle';
  }
}
```

## 6) Review and Adoption Loop

1. Evaluate each imported pattern against Product Scope + Roadmap phase targets.
2. Prototype behind feature flags where behavior risk is medium/high.
3. Measure with reliability/performance/quality checkpoints.
4. Promote successful patterns into engineering standards and onboarding tasks.

## 7) Research References

- https://nextjs.org/docs
- https://nodejs.org/en/docs/guides
- https://opentelemetry.io/docs/
- https://owasp.org/www-project-api-security/
- https://github.com/freeCodeCamp/freeCodeCamp
- https://github.com/TryGhost/Ghost
- https://github.com/excalidraw/excalidraw
- https://github.com/alan2207/bulletproof-react
- https://github.com/alan2207/awesome-codebases
