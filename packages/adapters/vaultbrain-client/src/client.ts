/**
 * PRX-25-EPIC-01 — High-level vaultbrain client.
 *
 * Public surface consumed by every module engine + the apps/web shell.
 * Each method is zod-validated end to end (request via schema infer +
 * response via runtime parse).
 *
 * Construction:
 *   const client = createVaultbrainClient({
 *     httpUrl: 'https://vaultbrain.njz-os.app',
 *     bearerToken: () => identity.getToken(),
 *   });
 *   await client.currentUser();
 *
 * Offline path: methods that mutate (startSession, completeSession,
 * recordEvent, recordReview, upsertManuscript) enqueue if the call
 * rejects with `VaultbrainNetworkError.retryable === true`. The queue
 * drains on the next successful call.
 */

import { createHttpClient, VaultbrainNetworkError } from './http';
import { createInMemoryQueue, uuidV7, type QueueStore } from './queue';
import {
  cardsListResponseSchema,
  cognitiveProfileSchema,
  completeSessionResponseSchema,
  manuscriptUpsertResponseSchema,
  progressionResponseSchema,
  recordEventResponseSchema,
  reviewResponseSchema,
  startSessionResponseSchema,
  streakStateSchema,
  userSchema,
  type Card,
  type CognitiveProfile,
  type CompleteSessionRequest,
  type CompleteSessionResponse,
  type Manuscript,
  type ManuscriptUpsertResponse,
  type ProgressionResponse,
  type RecordEventRequest,
  type RecordEventResponse,
  type ReviewRequest,
  type ReviewResponse,
  type StartSessionRequest,
  type StartSessionResponse,
  type User,
} from './schemas';
import type { z } from 'zod';
import type { StreakState } from '@njz-os/core';

export interface VaultbrainClientConfig {
  httpUrl: string;
  wsUrl?: string;
  bearerToken: () => string | Promise<string>;
  fetchImpl?: typeof fetch;
  queue?: QueueStore;
}

export interface VaultbrainClient {
  currentUser(signal?: AbortSignal): Promise<User>;
  getProgression(userId: string, signal?: AbortSignal): Promise<ProgressionResponse>;
  startSession(
    req: Omit<StartSessionRequest, 'idempotencyKey'>,
    signal?: AbortSignal
  ): Promise<StartSessionResponse>;
  completeSession(
    req: Omit<CompleteSessionRequest, 'idempotencyKey'>,
    signal?: AbortSignal
  ): Promise<CompleteSessionResponse>;
  recordEvent(
    req: Omit<RecordEventRequest, 'idempotencyKey'>,
    signal?: AbortSignal
  ): Promise<RecordEventResponse>;
  getStreaks(userId: string, signal?: AbortSignal): Promise<StreakState>;
  getCognitiveProfile(userId: string, signal?: AbortSignal): Promise<CognitiveProfile>;
  upsertManuscript(
    m: Omit<Manuscript, 'updatedAt'>,
    signal?: AbortSignal
  ): Promise<ManuscriptUpsertResponse>;
  listCards(deckSlug: string, signal?: AbortSignal): Promise<Card[]>;
  recordReview(
    req: Omit<ReviewRequest, 'idempotencyKey'>,
    signal?: AbortSignal
  ): Promise<ReviewResponse>;
  queueSize(): Promise<number>;
}

export function createVaultbrainClient(config: VaultbrainClientConfig): VaultbrainClient {
  const http = createHttpClient({
    baseUrl: config.httpUrl,
    bearerToken: config.bearerToken,
    fetchImpl: config.fetchImpl,
  });
  const queue = config.queue ?? createInMemoryQueue();

  const withQueueOnNetFail = async <T>(
    kind: string,
    payload: unknown,
    fn: () => Promise<T>
  ): Promise<T> => {
    try {
      return await fn();
    } catch (err) {
      if (err instanceof VaultbrainNetworkError && err.retryable) {
        await queue.enqueue({
          id: uuidV7(),
          kind,
          payload,
          enqueuedAt: new Date().toISOString(),
          attempts: 0,
        });
      }
      throw err;
    }
  };

  return {
    async currentUser(signal) {
      return http.call({
        method: 'GET',
        path: '/users/me',
        responseSchema: userSchema,
        signal,
      });
    },

    async getProgression(userId, signal) {
      return http.call({
        method: 'GET',
        path: `/users/${encodeURIComponent(userId)}/progression`,
        responseSchema: progressionResponseSchema,
        signal,
      });
    },

    async startSession(req, signal) {
      const body = { ...req, idempotencyKey: uuidV7() };
      return withQueueOnNetFail('session.start', body, () =>
        http.call({
          method: 'POST',
          path: '/sessions/start',
          body,
          responseSchema: startSessionResponseSchema,
          signal,
          isIdempotent: true,
        })
      );
    },

    async completeSession(req, signal) {
      const body = { ...req, idempotencyKey: uuidV7() };
      return withQueueOnNetFail('session.complete', body, () =>
        http.call({
          method: 'POST',
          path: `/sessions/${encodeURIComponent(req.sessionId)}/complete`,
          body,
          responseSchema: completeSessionResponseSchema,
          signal,
          isIdempotent: true,
        })
      );
    },

    async recordEvent(req, signal) {
      const body = { ...req, idempotencyKey: uuidV7() };
      return withQueueOnNetFail('event.record', body, () =>
        http.call({
          method: 'POST',
          path: '/events',
          body,
          responseSchema: recordEventResponseSchema,
          signal,
          isIdempotent: true,
        })
      );
    },

    async getStreaks(userId, signal) {
      return http.call({
        method: 'GET',
        path: `/users/${encodeURIComponent(userId)}/streaks`,
        responseSchema: streakStateSchema as unknown as z.ZodType<StreakState>,
        signal,
      });
    },

    async getCognitiveProfile(userId, signal) {
      return http.call({
        method: 'GET',
        path: `/users/${encodeURIComponent(userId)}/cognitive-profile`,
        responseSchema: cognitiveProfileSchema,
        signal,
      });
    },

    async upsertManuscript(m, signal) {
      const body = { manuscript: m, idempotencyKey: uuidV7() };
      return withQueueOnNetFail('manuscript.upsert', body, () =>
        http.call({
          method: 'PUT',
          path: `/manuscripts/${encodeURIComponent(m.id)}`,
          body,
          responseSchema: manuscriptUpsertResponseSchema,
          signal,
          isIdempotent: true,
        })
      );
    },

    async listCards(deckSlug, signal) {
      const res = await http.call({
        method: 'GET',
        path: `/decks/${encodeURIComponent(deckSlug)}/cards`,
        responseSchema: cardsListResponseSchema,
        signal,
      });
      return res.cards;
    },

    async recordReview(req, signal) {
      const body = { ...req, idempotencyKey: uuidV7() };
      return withQueueOnNetFail('card.review', body, () =>
        http.call({
          method: 'POST',
          path: `/cards/${encodeURIComponent(req.cardId)}/reviews`,
          body,
          responseSchema: reviewResponseSchema,
          signal,
          isIdempotent: true,
        })
      );
    },

    async queueSize() {
      return queue.size();
    },
  };
}
