[Ver001.000]

# SCHEMA_REGISTRY — NJZ RAT-OS

Single source of truth for canonical domain types. **Check here before defining a new type.** If it's missing, add it via PR — do not invent ad-hoc duplicates.

## Identity

| Type | Location | Notes |
|------|----------|-------|
| `UserId` | `@njz-os/core/src/identity.ts` | Brand: `string & { __userId: true }` |
| `SessionId` | `@njz-os/core/src/identity.ts` | UUID v7 |
| `WorldId` | `@njz-os/core/src/identity.ts` | PolyCo.World instance |

## Progression

| Type | Location | Notes |
|------|----------|-------|
| `StreakState` | `@njz-os/core/src/progression.ts` | `{ currentDays, longestDays, lastActiveAt }` |
| `XpTotals` | `@njz-os/core/src/progression.ts` | Per-module XP buckets |
| `ProgressionEvent` | `@njz-os/core/src/progression.ts` | Discriminated union over module emitters |
| `Reward` | `@njz-os/core/src/progression.ts` | Decoration / currency / aura unlock |

## Cognitive Profile

| Type | Location | Notes |
|------|----------|-------|
| `CognitiveProfile` | `@njz-os/analytics/src/profile.ts` | 5-dimension vector: memory, attention, speed, flexibility, spatial |
| `Percentile` | `@njz-os/analytics/src/profile.ts` | 0–100 against age cohort |
| `WorkoutPlan` | `@njz-os/analytics/src/workout.ts` | 3-game daily plan from adaptive engine |

## Focus (Lane A · PR #32)

| Type | Location | Notes |
|------|----------|-------|
| `FocusSession` | `@njz-os/focus-engine/src/session.ts` | Persistence row (mirrors vaultbrain `sessions` table) |
| `SessionMode` | `@njz-os/focus-engine/src/modes.ts` | `'pomodoro_25_5' \| 'deep_work_50_10' \| 'sprint_15_3' \| 'flow_90_20'` |
| `MODE_DEFINITIONS` | `@njz-os/focus-engine/src/modes.ts` | Per-mode `workMs` + `breakMs` per ADR-0009 |
| `FocusContext` | `@njz-os/focus-engine/src/machine.ts` | Reducer state: status + phase + startedAtMs + pausedMs + completion counts |
| `FocusEvent` | `@njz-os/focus-engine/src/machine.ts` | Discriminated union: `START`, `PAUSE`, `RESUME`, `NEXT_PHASE`, `COMPLETE`, `ABANDON` |
| `FocusPhase` | `@njz-os/focus-engine/src/machine.ts` | `'work' \| 'break'` |
| `FocusStatus` | `@njz-os/focus-engine/src/machine.ts` | `'pending' \| 'running' \| 'paused' \| 'completed' \| 'abandoned'` |
| `BlockerSettings` | `@njz-os/focus-engine/src/blocker.ts` | Enforcement level + whitelist + override policy |
| `BlockSchedule` (base) | `@njz-os/focus-engine/src/blocker.ts` | Common discriminator |
| `AnyBlockSchedule` | `@njz-os/focus-engine/src/schedule.ts` | Union of `RecurringDailySchedule` / `RecurringWeeklySchedule` / `OneTimeSchedule` / `FocusSyncSchedule` (Lane D · PR #36) |
| `EnforcementLevel` | `@njz-os/focus-engine/src/blocker.ts` | `'gentle' \| 'moderate' \| 'strict' \| 'maximum'` |

## Audio (Lane B · PR #34)

| Type | Location | Notes |
|------|----------|-------|
| `Soundscape` | `@njz-os/audio-engine/src/soundscape.ts` | Catalogue row (vs runtime manifest) |
| `BASELINE_SOUNDSCAPES` | `@njz-os/audio-engine/src/soundscape.ts` | 5 Phase-1 baseline scapes |
| `SoundscapeManifest` | `@njz-os/audio-engine/src/manifest.ts` | zod-validated runtime manifest (stems + codecs + crossfade window) |
| `Stem` / `StemFile` / `Codec` | `@njz-os/audio-engine/src/manifest.ts` | Per-stem files + codec preference (AAC > Ogg > Opus > MP3) |
| `BinauralPreset` | `@njz-os/audio-engine/src/binaural.ts` | `{ id, band, carrierHz, beatHz, durationMs }` |
| `DEFAULT_PRESETS` | `@njz-os/audio-engine/src/binaural.ts` | One preset per band: delta/theta/alpha/beta/gamma |
| `FrequencyBand` | `@njz-os/audio-engine/src/binaural.ts` | `'delta' \| 'theta' \| 'alpha' \| 'beta' \| 'gamma'` |
| `CrossfadeWindow` | `@njz-os/audio-engine/src/scheduler.ts` | Per-cycle gain keyframes for one stem |
| `CrossfadeKeyframe` | `@njz-os/audio-engine/src/scheduler.ts` | `{ timeSec, gain }` |
| `AudioGraph` | `@njz-os/audio-engine/src/graph.ts` | Static topology descriptor for docs |
| `PHASE_1_GRAPH` | `@njz-os/audio-engine/src/graph.ts` | Canonical Phase-1 topology per ADR-0010 §3 |
| `AudioEngine` | `@njz-os/audio-engine/src/graph.ts` | Runtime factory return: master gain + analyser + limiter + createStemGain / createBinauralLane |

## PolyCo.World (Lane C · PR #35)

| Type | Location | Notes |
|------|----------|-------|
| `Scene` | `@njz-os/polyworld/src/scene.ts` | Tilemap + decorations + actors |
| `SceneJson` | `@njz-os/polyworld/src/scene-loader.ts` | zod-validated scene file shape |
| `Decoration` | `@njz-os/polyworld/src/decoration.ts` | Placed item (sprite, position, unlockedBy rule) |
| `DecorationUnlockRule` | `@njz-os/polyworld/src/scene-loader.ts` | Parsed rule: `{ eventKind, moduleFilter?, threshold }` |
| `Actor` | `@njz-os/polyworld/src/actor.ts` | Hero / NPC |
| `Tile` | `@njz-os/polyworld/src/tile.ts` | Isometric tile primitive |
| `TileGrid` | `@njz-os/polyworld/src/tile.ts` | `(Tile \| null)[][]` |
| `IsoPoint` / `ScreenOrigin` | `@njz-os/polyworld/src/iso.ts` | Iso projection types |
| `Context2DLike` | `@njz-os/polyworld/src/renderer.ts` | Test-friendly subset of `CanvasRenderingContext2D` |
| `SpriteResolver` | `@njz-os/polyworld/src/renderer.ts` | `(spriteId) => frame \| null` lookup |
| `RendererStats` | `@njz-os/polyworld/src/renderer.ts` | Per-tick render stats |

## Pixel-art (Lane C · PR #35)

| Type | Location | Notes |
|------|----------|-------|
| `AsepriteManifest` | `@njz-os/pixel-art/src/loader.ts` | zod-validated Aseprite JSON output |
| `SpriteSheetDescriptor` | `@njz-os/pixel-art/src/loader.ts` | Parsed manifest + frame map |
| `ResolvedSpriteFrame` | `@njz-os/pixel-art/src/loader.ts` | Frame coordinates after lookup |

## Writing

| Type | Location | Notes |
|------|----------|-------|
| `Manuscript` | `@njz-os/writing/src/manuscript.ts` | Title, chapters, target, deadline |
| `Chapter` | `@njz-os/writing/src/manuscript.ts` | Status, wordCount, content (markdown) |
| `ExportFormat` | `@njz-os/writing/src/export.ts` | `'pdf' \| 'epub' \| 'docx' \| 'md' \| 'txt'` |

## Learning

| Type | Location | Notes |
|------|----------|-------|
| `Card` | `@njz-os/learning-cards/src/card.ts` | Illustration, headline, insight, detail |
| `Deck` | `@njz-os/learning-cards/src/deck.ts` | Ordered cards + metadata |
| `ReviewSchedule` | `@njz-os/learning-cards/src/spaced-repetition.ts` | SM-2-style schedule |

## Adapters / Transport

| Type | Location | Notes |
|------|----------|-------|
| `VaultbrainEvent` | `packages/adapters/vaultbrain-client/src/types.ts` | Mirrors upstream `@njz/vaultbrain-events` |
| `AgentRequest` | `packages/adapters/agent-gateway-client/src/types.ts` | Mirrors upstream contract |
| `ApiUser` | `packages/adapters/api-client/src/generated/` | Generated from OpenAPI; do not hand-edit |

### Vaultbrain client (PRX-25-EPIC-01 · PR #27)

| Type | Location | Notes |
|------|----------|-------|
| `VaultbrainClient` | `packages/adapters/vaultbrain-client/src/client.ts` | High-level surface: currentUser, getProgression, startSession, completeSession, recordEvent, getStreaks, getCognitiveProfile, upsertManuscript, listCards, recordReview, queueSize |
| `HttpClient` | `packages/adapters/vaultbrain-client/src/http.ts` | Fetch wrapper with retry + abort + observability |
| `VaultbrainNetworkError` / `VaultbrainHttpError` / `VaultbrainContractError` | `packages/adapters/vaultbrain-client/src/http.ts` | Typed error classes |
| `QueuedItem` / `QueueStore` | `packages/adapters/vaultbrain-client/src/queue.ts` | Offline queue (in-memory; IDB backing via ENH-01) |
| `CacheStore` / `CacheEntry` / `CacheKind` | `packages/adapters/vaultbrain-client/src/cache.ts` | Read-through cache with per-resource TTL (PRX-25-ENH-01 · PR #28) |
| `User` / `ProgressionResponse` / `Manuscript` / `Card` / `ReviewRequest` / etc. | `packages/adapters/vaultbrain-client/src/schemas.ts` | zod-inferred payload types |

### Identity client (Lane E · PR #30)

| Type | Location | Notes |
|------|----------|-------|
| `IdentityProvider` | `packages/adapters/identity-client/src/provider.ts` | Provider interface (currentSession, requestMagicLink, passkey lifecycle, signOut, deleteAccount) |
| `IdentityClient` | `packages/adapters/identity-client/src/index.ts` | High-level client wrapping a provider |
| `IdentityUser` | `packages/adapters/identity-client/src/types.ts` | zod-validated identity row (`id`, `email`, `displayName?`, `emailVerified`, `tier`, `createdAt`) |
| `AuthSession` | `packages/adapters/identity-client/src/types.ts` | zod-validated session (`user`, `expiresAt`, `refreshHintMs`) |
| `Tier` | `packages/adapters/identity-client/src/types.ts` | `'free' \| 'premium' \| 'team'` |
| `IdentityError` | `packages/adapters/identity-client/src/types.ts` | Typed error with code enum (UNAUTHORIZED / CHALLENGE_REJECTED / PROVIDER_ERROR / …) |
| `PasskeyEnrollmentChallenge` / `PasskeyAssertionChallenge` | `packages/adapters/identity-client/src/types.ts` | WebAuthn challenge payloads |
| `MagicLinkRequestOptions` | `packages/adapters/identity-client/src/types.ts` | `{ email, redirectTo? }` |

## Event Bus (PRX-25-PATCH-01)

| Type | Location | Notes |
|------|----------|-------|
| `EventBus<EventMap>` | `@njz-os/core/src/events.ts` | Generic typed pub/sub; synchronous dispatch; per-listener error isolation |
| `NjzEventMap` | `@njz-os/core/src/events.ts` | Canonical event-name → payload map; subscriber + emitter share types |
| `defaultEventBus` | `@njz-os/core/src/events.ts` | Shared singleton instance every module consumes |

Registered event names (`NjzEventMap` keys):

- `progression.event` — payload `ProgressionEvent` (from progression)
- `vaultbrain-client.request` / `.response` / `.error` / `.ws-state-change` — EPIC-01 observability
- `toast.show` / `toast.dismiss` — PATCH-05 surface
- `errorBoundary.caught` — PATCH-03 surface

Adding a new event:
1. Append to `NjzEventMap` in `events.ts`.
2. Add a row in this section.
3. Land producer + consumer in the same PR with tests on both sides.

## Reserved (Do Not Use Until Module Lands)

These are referenced in module specs but not yet implemented. Add the type when you build the module.

- `SeasonalEventConfig` (Phase 3)
- `FriendVisitInvite` (Phase 3)
- `CreatorAsset` (Phase 5)
- `MarketplaceListing` (Phase 5)

## Update Procedure

1. Adding a type → PR that updates this file + the source file in the same commit.
2. Renaming a type → PR that updates this file + all callsites + the source file.
3. Deprecating a type → mark `@deprecated` in source, leave entry here with `(deprecated)` tag, ADR explaining why.

## Cross-Repo Types (from `@njz/*`)

Types defined upstream in `notbleaux/ZeSporteXte`:

- `@njz/ui` design tokens — re-exported from `@njz-os/ui`.
- `@njz/vaultbrain-events` (planned) — wrapped by `packages/adapters/vaultbrain-client`.
- `@njz/agent-protocol` (planned) — wrapped by `packages/adapters/agent-gateway-client`.

Do not re-define these here. Import them through the adapter layer.
