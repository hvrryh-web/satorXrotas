# SATOR Data Partition Firewall Policy

## Purpose

SATOR is a two-part esports platform:

1. **RadiantX** — An offline, deterministic tactical FPS simulation game (Godot 4 / GDScript)
2. **SATOR Web** — An online stats platform showing public match statistics

The **firewall** is the technical and policy boundary that prevents game-internal
simulation data from ever reaching the public web platform. This document defines what
that boundary looks like, how it is enforced, and what to do when it is violated.

---

## Firewall Rule Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     GAME SIMULATION                          │
│  MatchEngine · Agent · DuelResolver · RaycastDuelEngine      │
│                                                              │
│  Contains: radarData, simulationTick, seedValue,             │
│            internalAgentState, visionConeData, ...           │
└─────────────────────────┬────────────────────────────────────┘
                          │  ALL data passes through here
                          ▼
          ┌───────────────────────────┐
          │    FantasyDataFilter      │  ◄─── packages/data-partition-lib
          │    .sanitizeForWeb()      │
          └───────────────┬───────────┘
                          │  Only PUBLIC fields pass
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                     API LAYER                                │
│  Validates response against @sator/stats-schema types        │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                   SATOR WEB PLATFORM                         │
│  Displays only public stats — no game internals              │
└──────────────────────────────────────────────────────────────┘
```

---

## Data Classification

### PUBLIC Fields (allowed on web)

These fields may appear in API responses and web UI:

| Field | Type | Description |
|-------|------|-------------|
| `kills` | `number` | Total kills in match |
| `deaths` | `number` | Total deaths in match |
| `assists` | `number` | Total assists in match |
| `damage` | `number` | Total damage dealt |
| `headshots` | `number` | Headshot kills |
| `utilityDamage` | `number` | Grenade / ability damage |
| `roundsWon` | `number` | Rounds won by player's team |
| `firstKills` | `number` | First kills per round |
| `clutchesWon` | `number` | Clutch rounds won |
| `matchId` | `string` | Public match identifier |
| `playerId` | `string` | Public player identifier |
| `mapName` | `string` | Map played on |
| `startedAt` | `string` | Match start time (ISO 8601) |
| `endedAt` | `string` | Match end time (ISO 8601) |
| `winnerSide` | `string` | Winning team side |
| `roundsPlayed` | `number` | Total rounds in match |
| `username` | `string` | Player display name |
| `rankTier` | `string` | Current rank tier |
| `rankPoints` | `number` | Current rank points |
| `region` | `string` | Player region |

For the authoritative list, see `packages/stats-schema/src/types/`.

---

### GAME-ONLY Fields (permanently blocked)

These fields must **never** appear in any API response, web page, or public database:

| Field | Risk | Source |
|-------|------|--------|
| `internalAgentState` | Exposes AI decision tree; enables counter-play scripting | `Agent.gd` |
| `radarData` | Real-time position feed; enables wall-hack bots | `MatchEngine.gd` |
| `detailedReplayFrameData` | Per-tick simulation frames; enables full replay extraction | `EventLog.gd` |
| `simulationTick` | Engine internal counter; reveals match pacing | `MatchEngine.gd` |
| `seedValue` | RNG seed; allows match outcome prediction | `MatchEngine.gd` |
| `visionConeData` | Agent vision state; reveals what AI can see | `Agent.gd` |
| `smokeTickData` | Smoke utility simulation state | `Agent.gd` |
| `recoilPattern` | Per-weapon recoil data; enables aimbot scripting | `WeaponState.gd` |

These are encoded in `FantasyDataFilter.GAME_ONLY_FIELDS` in
`packages/data-partition-lib/src/FantasyDataFilter.ts`.

---

## Enforcement Points

The firewall is enforced at **four points**. All four must pass for data to reach the
web.

### Point 1 — Game Extraction (`LiveSeasonModule.gd`)

The game extracts only public stats before sending them to the API:

```gdscript
# apps/radiantx-game/src/LiveSeasonModule.gd (Phase 2)
func extract_public_stats(match_result: MatchResult) -> Dictionary:
    var raw = {
        "kills": match_result.kills,
        "deaths": match_result.deaths,
        "assists": match_result.assists,
        "damage": match_result.damage,
        # NOTE: Do NOT include seedValue, simulationTick, radarData, etc.
    }
    return raw
```

### Point 2 — API Middleware Filter (TypeScript)

The API middleware strips any game-only fields that slipped through Point 1:

```typescript
// api/src/middleware/firewallMiddleware.ts (Phase 3)
import { FantasyDataFilter } from '@sator/data-partition-lib';

export function firewallMiddleware(req, res, next) {
  try {
    const sanitized = FantasyDataFilter.sanitizeForWeb(req.body);
    req.body = sanitized;
    next();
  } catch (err) {
    res.status(400).json({ error: 'Firewall: ' + err.message });
  }
}
```

### Point 3 — Web Schema Validation (TypeScript)

The web platform validates all data against `@sator/stats-schema` types:

```typescript
// apps/sator-web/src/lib/validateStats.ts (Phase 3)
import type { Statistics } from '@sator/stats-schema';

function assertIsStatistics(data: unknown): asserts data is Statistics {
  // Runtime validation — throw if unexpected fields found
  const allowed = new Set(['playerId', 'matchId', 'kills', 'deaths',
    'assists', 'damage', 'headshots', 'utilityDamage',
    'roundsWon', 'firstKills', 'clutchesWon']);
  for (const key of Object.keys(data as object)) {
    if (!allowed.has(key)) {
      throw new Error(`Unexpected field in web data: ${key}`);
    }
  }
}
```

### Point 4 — CI/CD Testing

Automated tests run on every PR to `main` and `develop`:

```yaml
# .github/workflows/test-firewall.yml
- name: Run firewall tests
  run: npm run test:firewall
```

Tests verify:
- All `GAME_ONLY_FIELDS` are stripped by `sanitizeForWeb()`
- `validateWebInput()` throws on every forbidden field
- Clean data passes validation without error

---

## Violation Detection and Response

### How violations are detected

1. **CI fails** — `test:firewall` catches field leakage in automated tests
2. **TypeScript errors** — Schema package type mismatch surfaced at compile time
3. **Runtime errors** — `validateWebInput()` throws in API middleware
4. **Code review** — CODEOWNERS requires `@hvrryh-web` review on firewall changes

### Response procedure

| Severity | Condition | Action |
|----------|-----------|--------|
| **Critical** | `GAME_ONLY_FIELDS` found in production DB | Immediate rollback; audit all recent deployments |
| **High** | Field leaks through API but not yet in DB | Block deploy; fix middleware; re-run tests |
| **Medium** | Field present in game extraction but caught by middleware | Fix `LiveSeasonModule.gd`; add regression test |
| **Low** | CI test detects new unlisted field | Add field to `GAME_ONLY_FIELDS` if game-internal; add to schema if public |

---

## Decision Tree: Adding a New Stat

```
New stat needed?
     │
     ▼
Is it derived from game simulation internals?
  (tick data, AI state, seed, vision, recoil)
     │
     ├─ YES → It is GAME-ONLY. Do NOT add to stats-schema.
     │         Add to FantasyDataFilter.GAME_ONLY_FIELDS if
     │         it might accidentally appear in extracted data.
     │
     └─ NO  → Is it meaningful to end users?
                   │
                   ├─ YES → Add to stats-schema types.
                   │         Add to PUBLIC fields table above.
                   │         Update web UI and API response.
                   │
                   └─ NO  → Do not add it anywhere.
```

---

## FAQ

**Q: Can I add `simulationTick` to the web API for debugging purposes?**
A: No. Debugging access to simulation internals must go through a separate,
   private admin API that never touches the public web platform.

**Q: What if a field is useful for analytics but isn't shown on the web?**
A: If it doesn't appear in `@sator/stats-schema`, it cannot be stored in the public
   database. Create a separate private analytics pipeline that does not share
   infrastructure with the web platform.

**Q: Is `replayData` the same as `detailedReplayFrameData`?**
A: `detailedReplayFrameData` refers to the per-tick simulation frames that include
   internal state. A summary of match events (round scores, kill feed) would be
   permissible if defined in `stats-schema`. Full frame-by-frame replay data is
   always blocked.

**Q: Can the web platform link to a downloadable replay file?**
A: Only if the replay file is stripped of `GAME_ONLY_FIELDS` before upload. Full
   simulation replays (with seed and tick data) must not be publicly accessible.

**Q: Who can approve changes to `GAME_ONLY_FIELDS`?**
A: Only `@hvrryh-web` (see `.github/CODEOWNERS`). Any change to the field list
   requires explicit justification in the PR description.

**Q: Does the firewall apply to internal tooling (dashboards, admin panels)?**
A: Internal tools are out of scope for this firewall policy but should follow the
   principle of least privilege. Game internals should only be accessible by
   authenticated admin users, never anonymously.

---

## Audit Checklist Before Deployment

Run through this checklist before any production deployment that touches data flow:

- [ ] `npm run test:firewall` passes with zero failures
- [ ] `npm run validate:schema` passes — no new fields in schema
- [ ] No `GAME_ONLY_FIELDS` keys appear in any API response body (manual spot-check)
- [ ] `packages/data-partition-lib/src/FantasyDataFilter.ts` has not been modified
      without an approved PR from `@hvrryh-web`
- [ ] All new stat fields are documented in the PUBLIC fields table above
- [ ] TypeScript compilation passes with no errors in schema and firewall packages
- [ ] Database migration scripts do not create columns named after `GAME_ONLY_FIELDS`

---

*Last updated: Phase 1 — foundation. Update this document in Phase 3 when full
implementation is complete.*
