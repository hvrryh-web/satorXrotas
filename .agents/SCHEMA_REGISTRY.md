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

## Focus

| Type | Location | Notes |
|------|----------|-------|
| `FocusSession` | `@njz-os/focus-engine/src/session.ts` | Pomodoro / deep-work session record |
| `SessionMode` | `@njz-os/focus-engine/src/session.ts` | `'pomodoro_25_5' \| 'deep_work_50_10' \| ...` |
| `BlockerSettings` | `@njz-os/focus-engine/src/blocker.ts` | Apps/sites + enforcement level |

## Audio

| Type | Location | Notes |
|------|----------|-------|
| `Soundscape` | `@njz-os/audio-engine/src/soundscape.ts` | Track metadata + manifest |
| `BinauralPreset` | `@njz-os/audio-engine/src/binaural.ts` | Carrier + beat Hz + duration |
| `AudioGraph` | `@njz-os/audio-engine/src/graph.ts` | Web Audio node graph descriptor |

## PolyCo.World

| Type | Location | Notes |
|------|----------|-------|
| `Scene` | `@njz-os/polyworld/src/scene.ts` | Tilemap + decorations + actors |
| `Decoration` | `@njz-os/polyworld/src/decoration.ts` | Placed item (origin, sprite, tags) |
| `Actor` | `@njz-os/polyworld/src/actor.ts` | Hero / NPC |
| `Tile` | `@njz-os/polyworld/src/tile.ts` | Isometric tile primitive |

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
