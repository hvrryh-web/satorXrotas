# PixelOffice Agent Modular Design

## Module Boundaries
1. **Sprite UI Module** (`ui-sprite-kit`)
   - Avatar rendering and animation state machine
   - UI state hooks (status, alerts, coach moments)
2. **Planner Workflow Module** (`planner-core`)
   - Task lifecycle, dependency graph, sprint and milestone tracking
3. **Simulation Module** (`planner-core` + service layer)
   - Manager-sim mechanics: morale, velocity, risk, delivery score
4. **AI Adapter Module** (`ai-adapter`)
   - Provider abstraction and prompt/response normalization
   - Action guardrails and audit metadata

## Interaction Model
- Planner state emits events.
- Sprite module maps events to behavior cues.
- AI adapter proposes actions.
- User approves or rejects actions in WebApp.

## Gameplay-Inspired PM Mechanics
- Project health score
- Agent workload meter
- Milestone pressure events
- Coaching prompts for newcomer actions
