export interface ApiClientConfig {
  baseUrl: string;
  bearerToken?: () => string | Promise<string>;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export interface ApiClient {
  health(): Promise<{ status: 'ok'; version: string; commit: string }>;
}

/** Phase 0 stub. Generated client lands in src/generated/ in Phase 1+. */
export function createApiClient(config: ApiClientConfig): ApiClient {
  return {
    async health() {
      const res = await fetch(`${config.baseUrl}/health`);
      if (!res.ok) {
        throw new ApiError(`health check failed: ${res.status}`, res.status);
      }
      return (await res.json()) as { status: 'ok'; version: string; commit: string };
    },
  };
}
