import type { UserId } from '@njz-os/core';

export interface VaultbrainConfig {
  httpUrl: string;
  wsUrl: string;
  bearerToken: () => string | Promise<string>;
}

export interface VaultbrainEvent<P = unknown> {
  kind: string;
  userId: UserId;
  at: string;
  payload: P;
}

export class VaultbrainError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
  ) {
    super(message);
    this.name = 'VaultbrainError';
  }
}
