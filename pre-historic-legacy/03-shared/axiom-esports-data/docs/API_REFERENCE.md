# API_REFERENCE.md — REST Endpoint Documentation

Base URL: `http://localhost:8000` (development)

## Players

### GET /api/players/{player_id}
Get a single player's current stats and investment grade.

**Response:**
```json
{
  "player_id": "uuid",
  "name": "string",
  "team": "string",
  "region": "Americas",
  "role": "Entry",
  "kills": 18,
  "acs": 265.4,
  "sim_rating": 1.23,
  "rar_score": 1.15,
  "investment_grade": "A",
  "confidence_tier": 75.0,
  "map_count": 87
}
```

### GET /api/players/
List players with filters.

**Query parameters:**
- `region` — Filter by region
- `role` — Filter by role
- `min_maps` — Minimum map count (default: 50)
- `grade` — Investment grade filter (`A+`, `A`, `B`, `C`, `D`)
- `limit` — Max results (default: 50, max: 200)
- `offset` — Pagination offset

## Analytics

### GET /api/analytics/simrating/{player_id}
Get SimRating breakdown for a player.

**Response:**
```json
{
  "sim_rating": 1.23,
  "components": {
    "kills": 0.28,
    "deaths_inverse": 0.18,
    "adjusted_kill_value": 0.30,
    "adr": 0.25,
    "kast_pct": 0.22
  },
  "season": "2025",
  "role": "Entry",
  "cohort_size": 142
}
```

### GET /api/analytics/rar/{player_id}
Get Role-Adjusted value above Replacement.

### GET /api/analytics/investment/{player_id}
Get investment grade with age curve and temporal decay factors.

## Matches (SATOR Spatial Data)

### GET /api/matches/{match_id}/rounds/{round_number}/sator-events
SATOR Layer 1 events (planters, MVPs, hotstreaks).

### GET /api/matches/{match_id}/rounds/{round_number}/arepo-markers
AREPO Layer 4 death stain markers.

### GET /api/matches/{match_id}/rounds/{round_number}/rotas-trails
ROTAS Layer 5 rotation trail data.
