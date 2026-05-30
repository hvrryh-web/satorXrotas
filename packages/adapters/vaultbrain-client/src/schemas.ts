/**
 * PRX-25-EPIC-01 — Zod schemas for the vaultbrain HTTP + WS surface.
 *
 * These mirror `contracts/openapi/njz-rat-os.yaml` (consumer spec). When
 * the upstream vaultbrain ships ADR-0008's user-state extension, regenerate
 * this file from the openapi via `pnpm contracts:generate` (TBD) and
 * commit alongside.
 *
 * Schema-first design: every inbound payload runs through one of these
 * schemas; failures throw `VaultbrainContractError` (in client.ts).
 */

import { z } from 'zod';

export const userIdSchema = z.string().min(1).brand('UserId');
export const sessionIdSchema = z.string().min(1).brand('SessionId');

export const moduleSlugSchema = z.enum([
  'focus-hero',
  'soundscapes',
  'distraction-blocker',
  'writing-space',
  'micro-learning',
  'brain-training',
  'polyco-world',
]);

export const userSchema = z.object({
  id: userIdSchema,
  email: z.string().email(),
  displayName: z.string().min(1),
  tier: z.enum(['free', 'premium', 'team']),
  timezone: z.string(),
  createdAt: z.string().datetime(),
});

export const streakStateSchema = z.object({
  currentDays: z.number().int().min(0),
  longestDays: z.number().int().min(0),
  lastActiveAt: z.string().datetime(),
});

export const progressionEventSchema = z.discriminatedUnion('kind', [
  z.object({
    kind: z.literal('session.start'),
    userId: userIdSchema,
    sessionId: sessionIdSchema,
    module: moduleSlugSchema,
    at: z.string().datetime(),
  }),
  z.object({
    kind: z.literal('session.complete'),
    userId: userIdSchema,
    sessionId: sessionIdSchema,
    module: moduleSlugSchema,
    durationMs: z.number().int().min(0),
    xpAwarded: z.number().int().min(0),
    at: z.string().datetime(),
  }),
  z.object({
    kind: z.literal('session.abandon'),
    userId: userIdSchema,
    sessionId: sessionIdSchema,
    module: moduleSlugSchema,
    at: z.string().datetime(),
  }),
  z.object({
    kind: z.literal('streak.extend'),
    userId: userIdSchema,
    module: moduleSlugSchema,
    newCurrent: z.number().int().min(0),
    at: z.string().datetime(),
  }),
  z.object({
    kind: z.literal('streak.break'),
    userId: userIdSchema,
    module: moduleSlugSchema,
    at: z.string().datetime(),
  }),
]);

export const progressionResponseSchema = z.object({
  totalXp: z.number().int().min(0),
  level: z.number().int().min(1),
  streak: streakStateSchema,
  recentEvents: z.array(progressionEventSchema).max(100),
});

export const startSessionRequestSchema = z.object({
  module: moduleSlugSchema,
  mode: z.string().min(1),
  startedAt: z.string().datetime(),
  idempotencyKey: z.string().uuid(),
});

export const startSessionResponseSchema = z.object({
  sessionId: sessionIdSchema,
  startedAt: z.string().datetime(),
});

export const completeSessionRequestSchema = z.object({
  sessionId: sessionIdSchema,
  endedAt: z.string().datetime(),
  durationMs: z.number().int().min(0),
  idempotencyKey: z.string().uuid(),
});

export const completeSessionResponseSchema = z.object({
  sessionId: sessionIdSchema,
  xpAwarded: z.number().int().min(0),
  streak: streakStateSchema,
});

export const recordEventRequestSchema = z.object({
  event: progressionEventSchema,
  idempotencyKey: z.string().uuid(),
});

export const recordEventResponseSchema = z.object({
  accepted: z.boolean(),
  serverAt: z.string().datetime(),
});

export const cognitiveProfileSchema = z.object({
  userId: userIdSchema,
  memory: z.number().min(0).max(100),
  attention: z.number().min(0).max(100),
  speed: z.number().min(0).max(100),
  flexibility: z.number().min(0).max(100),
  spatial: z.number().min(0).max(100),
  computedAt: z.string().datetime(),
});

export const cardSchema = z.object({
  id: z.string().min(1),
  deckSlug: z.string().min(1),
  front: z.string().min(1),
  back: z.string().min(1),
  interval: z.number().int().min(0),
  easeFactor: z.number().min(1),
  dueAt: z.string().datetime(),
});

export const cardsListResponseSchema = z.object({
  cards: z.array(cardSchema),
  totalCount: z.number().int().min(0),
});

export const reviewRequestSchema = z.object({
  cardId: z.string().min(1),
  quality: z.number().int().min(0).max(5),
  reviewedAt: z.string().datetime(),
  idempotencyKey: z.string().uuid(),
});

export const reviewResponseSchema = z.object({
  cardId: z.string().min(1),
  nextInterval: z.number().int().min(0),
  nextDueAt: z.string().datetime(),
});

export const manuscriptSchema = z.object({
  id: z.string().min(1),
  userId: userIdSchema,
  title: z.string(),
  body: z.string(),
  wordCount: z.number().int().min(0),
  updatedAt: z.string().datetime(),
});

export const manuscriptUpsertRequestSchema = z.object({
  manuscript: manuscriptSchema.omit({ updatedAt: true }),
  idempotencyKey: z.string().uuid(),
});

export const manuscriptUpsertResponseSchema = z.object({
  id: z.string().min(1),
  updatedAt: z.string().datetime(),
});

export type User = z.infer<typeof userSchema>;
export type ProgressionResponse = z.infer<typeof progressionResponseSchema>;
export type StartSessionRequest = z.infer<typeof startSessionRequestSchema>;
export type StartSessionResponse = z.infer<typeof startSessionResponseSchema>;
export type CompleteSessionRequest = z.infer<typeof completeSessionRequestSchema>;
export type CompleteSessionResponse = z.infer<typeof completeSessionResponseSchema>;
export type RecordEventRequest = z.infer<typeof recordEventRequestSchema>;
export type RecordEventResponse = z.infer<typeof recordEventResponseSchema>;
export type CognitiveProfile = z.infer<typeof cognitiveProfileSchema>;
export type Card = z.infer<typeof cardSchema>;
export type CardsListResponse = z.infer<typeof cardsListResponseSchema>;
export type ReviewRequest = z.infer<typeof reviewRequestSchema>;
export type ReviewResponse = z.infer<typeof reviewResponseSchema>;
export type Manuscript = z.infer<typeof manuscriptSchema>;
export type ManuscriptUpsertRequest = z.infer<typeof manuscriptUpsertRequestSchema>;
export type ManuscriptUpsertResponse = z.infer<typeof manuscriptUpsertResponseSchema>;
