# Interface Primitives + UX Acceptance Checklist

Use this checklist for planner/sprite UX increments in Phases B-D.

## UI State Primitives
- [ ] Planner task status primitive supports: todo, in_progress, blocked, done.
- [ ] Risk primitive supports: low, medium, high, critical.
- [ ] Approval-required primitive supports: none, pending_approval, approved, rejected.
- [ ] Status primitives include visible label + semantic color + icon/text fallback.

## Sprite State Mapping
- [ ] `task_assigned` maps to `advising` state.
- [ ] `risk_spike` maps to `warning` state.
- [ ] `milestone_hit` maps to `celebrating` state.
- [ ] Default/no-event maps to `idle`.

## Action Confirmation + Failure Flow
- [ ] High-impact actions present explicit confirmation before submission.
- [ ] Confirmation copy states consequence and rollback or mitigation path.
- [ ] Failures provide clear recovery choices (retry, cancel, escalate).
- [ ] Audit trace link is visible from action detail/failure message.

## Accessibility Acceptance
- [ ] Planner board and action controls are keyboard navigable.
- [ ] Modal/dialog open sets focus to first interactive element.
- [ ] Modal/dialog close returns focus to invoking control.
- [ ] Status updates are announced using accessible status messaging.

## UX Observability Events
- [ ] Emit `task_assignment_viewed` and `task_assignment_confirmed` events.
- [ ] Emit `action_approval_requested`, `action_approved`, `action_rejected` events.
- [ ] Emit `action_completed` and `action_failed` events.
- [ ] Include correlation ID when available to join UI/API telemetry.
