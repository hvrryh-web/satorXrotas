# @sator/stats-schema

> **Single source of truth for SATOR public statistics**

## Purpose

This package defines the TypeScript types for every piece of data that may appear on
the SATOR web platform. If a stat is not defined here, it is not public.

```
Game → FantasyDataFilter → API → @sator/stats-schema types → Web
```

## Constraint

> **All public stats flow through these types.**

Adding a field here is a deliberate editorial decision. Fields must be:
- Meaningful to end users
- Non-exploitable for fantasy/betting abuse
- Derivable from match results without exposing simulation internals

## ⚠️ Warning

> **Do NOT add game-internal fields here.**

The following are examples of fields that are **permanently banned** from this package:

| Field | Reason |
|-------|--------|
| `internalAgentState` | Exposes AI decision tree |
| `radarData` | Exposes real-time position feed |
| `detailedReplayFrameData` | Exposes per-tick simulation data |
| `simulationTick` | Exposes engine internals |
| `seedValue` | Allows match prediction |
| `visionConeData` | Exposes agent vision state |
| `smokeTickData` | Exposes utility simulation |
| `recoilPattern` | Exposes weapon internals |

See `docs/FIREWALL_POLICY.md` for the complete list and rationale.

## File Organization

```
src/
└── types/
    ├── index.ts       ← Re-exports all public types
    ├── Player.ts      ← Player identity and profile
    ├── Match.ts       ← Match metadata
    ├── Season.ts      ← Season and ranking data
    └── Statistics.ts  ← Performance stats
```

## Usage

```typescript
import type { Player, Match, Statistics } from '@sator/stats-schema';
```

## Building

```bash
npm run build
```

## Schema Validation

```bash
npm run validate:schema
```

Checks that no `GAME_ONLY_FIELDS` have been introduced into the type definitions.
