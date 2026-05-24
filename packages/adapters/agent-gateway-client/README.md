# @njz-os/adapters-agent-gateway-client

Thin client for upstream `services/agent-gateway`. Used by in-app AI helpers (e.g. writing suggestions, training recommendations).

## Phase 0

Stub returning `AgentGatewayError('NOT_IMPLEMENTED')`. Types defined.

## Phase 4 (when AI personalization layer lands)

- Streaming responses
- Tool-call routing
- User context injection (cognitive profile, recent sessions)
- Rate limiting per user
