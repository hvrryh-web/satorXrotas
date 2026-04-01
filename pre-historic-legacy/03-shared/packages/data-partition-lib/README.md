# @sator/data-partition-lib

> **Enforce data partition between SATOR game and web platform**

The data partition library is the technical heart of the SATOR firewall. It prevents
game-internal simulation data from leaking into the public web platform.

## Purpose

SATOR consists of two components:
1. **RadiantX** (offline game) — Runs full tactical simulation with detailed internal state
2. **SATOR Web** (online platform) — Displays only public match statistics

This library enforces the boundary between them.

```
Game Simulation
     │
     ▼
FantasyDataFilter.sanitizeForWeb()   ◄── Firewall enforcement point
     │
     ▼
API Layer → Web Platform
```

## Usage

### Sanitizing game data before sending to API

```typescript
import { FantasyDataFilter } from '@sator/data-partition-lib';

const rawGameData = matchEngine.extractStats(); // May contain internal fields
const safeData = FantasyDataFilter.sanitizeForWeb(rawGameData);
// safeData is now free of all GAME_ONLY_FIELDS
await api.post('/matches', safeData);
```

### Validating incoming web data

```typescript
import { FantasyDataFilter } from '@sator/data-partition-lib';

app.post('/api/matches', (req, res) => {
  try {
    FantasyDataFilter.validateWebInput(req.body); // Throws if forbidden field found
    await db.save(req.body);
    res.json({ ok: true });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});
```

## GAME_ONLY_FIELDS

The following fields are permanently blocked from the web platform:

| Field | Risk |
|-------|------|
| `internalAgentState` | Exposes AI decision tree |
| `radarData` | Real-time position feed |
| `detailedReplayFrameData` | Per-tick simulation data |
| `simulationTick` | Engine internal counter |
| `seedValue` | Allows match prediction / reproduction |
| `visionConeData` | Agent vision state |
| `smokeTickData` | Utility simulation state |
| `recoilPattern` | Weapon internal data |

See `docs/FIREWALL_POLICY.md` for the complete classification and rationale.

## Tests

Firewall tests live in `tests/firewall/`. Run with:

```bash
npm run test:firewall
```

Tests verify:
- All `GAME_ONLY_FIELDS` are stripped by `sanitizeForWeb()`
- `validateWebInput()` throws on any forbidden field
- Clean data passes validation without error

## Status

Phase 1 stub — full recursive implementation in Phase 3.
