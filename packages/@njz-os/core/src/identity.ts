export type UserId = string & { readonly __userId: unique symbol };
export type SessionId = string & { readonly __sessionId: unique symbol };
export type WorldId = string & { readonly __worldId: unique symbol };

export const userId = (s: string): UserId => s as UserId;
export const sessionId = (s: string): SessionId => s as SessionId;
export const worldId = (s: string): WorldId => s as WorldId;
