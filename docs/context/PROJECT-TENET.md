# Project TENET
## Agent Context: What We're Building

---

## ARCHITECTURE OVERVIEW

**TENET** is the meta-layer: WorldHUBs database connecting all game worlds.

```
TENET (Meta-Layer)
    ├── tenet-valorant (Game World)
    │       └── tezet (4 HUBs)
    │           ├── ROTAS — Stats Reference
    │           ├── SATOR — Advanced Analytics
    │           ├── OPERA — Pro Scene Info
    │           └── AREPO — Community Forums
    │
    └── tenet-cs2 (Game World)
            └── tezet (4 HUBs)
                ├── ROTAS — Stats Reference
                ├── SATOR — Advanced Analytics
                ├── OPERA — Pro Scene Info
                └── AREPO — Community Forums
```

---

## THE 4 HUBS

| HUB | Function | Color | Purpose |
|-----|----------|-------|---------|
| **ROTAS** | Stats Reference | [#TEA] Teal | Raw data, leaderboards, player profiles |
| **SATOR** | Advanced Analytics | [#TEA] Teal | Predictive models, machine learning |
| **OPERA** | Pro Scene Info | [#ORG] Orange | Tournaments, matches, schedules |
| **AREPO** | Community | [#ORG] Orange | Forums, discussions, fan content |

---

## TENET PORTAL (Entry Point)

**Route:** `/`

**Layout (Quadrant Modularity):**
```
┌─────────────────────────────────────────────┐
│          [TENET HEADER]                     │
├──────────────────┬──────────────────────────┤
│    [ROTAS]       │      [SATOR]             │
│    Stats Hub     │      Analytics Hub       │
│    [#TEA]        │      [#TEA]              │
├──────────────────┼──────────────────────────┤
│    [OPERA]       │      [AREPO]             │
│    Pro Scene     │      Community           │
│    [#ORG]        │      [#ORG]              │
├──────────────────┴──────────────────────────┤
│  [Valorant]        [CS2]                    │
│  Game Select       Game Select              │
└─────────────────────────────────────────────┘
```

**Constraints:**
- 4 HUB tiles ONLY (not 3, not 5)
- 2 Game tiles
- ZERO feature cards below (remove 4×2 grid)
- NO scroll (100vh max)

---

## WIREFRAME SITES

### Site 1: TENET Portal
**Route:** `/`
- Game selection gateway
- 4 HUB quadrant grid
- 2 Game selection tiles

### Site 2: Player Leaderboard
**Route:** `/valorant/stats/players`
- HLTV-style dense table
- Role filters, column customization
- Form dots, skeleton loading

### Site 3: Player Profile
**Route:** `/valorant/stats/players/:slug`
- Individual player deep-dive
- Career stats, agent pool
- Match history, tabs

---

## DESIGN SYSTEM (Strict)

### Colors
| Token | Hex | Usage |
|-------|-----|-------|
| bg-primary | #0A0A0A | Background |
| bg-secondary | #141414 | Cards |
| accent-teal | #14B8A6 | Data, ROTAS/SATOR |
| accent-orange | #F97316 | CTAs, OPERA/AREPO |
| accent-red | #FF4655 | LIVE badge, Valorant |
| text-primary | #F8FAFC | Headlines |
| text-secondary | #94A3B8 | Descriptions |

### Border Radius
- **DEFAULT:** 0px (sharp corners)
- **MAXIMUM:** 4px (interactive elements)
- **PROHIBITED:** 8px, 12px, 16px

### Typography
- **Headings:** Inter, 48px/36px/28px
- **Data:** JetBrains Mono (tabular nums)
- **Body:** Inter, 16px

### Shadows & Depth
- Cards: `0 4px 12px rgba(0,0,0,0.4)`
- Hover glow: `0 0 20px rgba(20,184,166,0.15)`
- Vignette masks: Mandatory on game tiles

---

## CURRENT SPRINT

**Status:** Wireframe v3 Implementation

**Deliverables:**
1. TENET Portal (IN PROGRESS)
2. Player Leaderboard (PENDING)
3. Player Profile (PENDING)

**Blockers:** None

**Next Review:** After TENET Portal CRIT

---

Context Version: 1.0.0
Last Updated: 2026-03-31
