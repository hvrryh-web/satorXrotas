export interface AgentGatewayConfig {
  httpUrl: string;
  bearerToken: () => string | Promise<string>;
}

export interface AgentRequest {
  prompt: string;
  context?: Record<string, unknown>;
  userId: string;
}

export interface AgentResponse {
  text: string;
  toolCalls?: { name: string; arguments: Record<string, unknown> }[];
}

export class AgentGatewayError extends Error {
  constructor(
    message: string,
    public readonly code: string,
  ) {
    super(message);
    this.name = 'AgentGatewayError';
  }
}

export interface AgentGatewayClient {
  ask(req: AgentRequest): Promise<AgentResponse>;
}

/** Phase 0 stub. */
export function createAgentGatewayClient(_config: AgentGatewayConfig): AgentGatewayClient {
  return {
    async ask() {
      throw new AgentGatewayError(
        'agent-gateway-client not implemented in Phase 0',
        'NOT_IMPLEMENTED',
      );
    },
  };
}
