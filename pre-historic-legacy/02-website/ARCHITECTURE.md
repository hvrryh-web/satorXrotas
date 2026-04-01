# SATOR eXe / ROTAS eXe — Platform Architecture

## Hierarchy

```
SATOR eXe (Parent Platform)
├── System Layer (Universal)
│   ├── User Authentication
│   ├── Quaternary Grid Engine
│   ├── Data Pipeline (Axiom)
│   └── Cross-Game Analytics
│
├── Game Profiles (Per-Game Layers)
│   ├── RadiantX — Valorant
│   ├── CounterX — Counter-Strike
│   ├── ApexX — Apex Legends
│   └── [Future Games]
│
└── Environment Layers (Per-Profile)
    ├── Visual Theme
    ├── Data Schema
    ├── Map Integration
    └── Agent/Weapon Rosters
```

## Design System: Two-Tier Approach

### Tier 1: SATOR Core (Universal)
- **Palette:** Payne's Grey, Electric Cyan, Porcelain White, Deep Navy
- **Grid:** Quaternary 2×2 (Q1-Q4)
- **Glass:** 88% opacity, blur(12px)
- **Typography:** Inter family

### Tier 2: Game Profile (Variable)
| Profile | Accent Color | Background | Signature Element |
|---------|--------------|------------|-------------------|
| RadiantX | Valorant Red (#ff4655) | Dark purple-black | Agent portraits |
| CounterX | CS Orange (#f7931e) | Military green-black | Weapon icons |
| ApexX | Apex Gold (#d4af37) | Frontier brown | Legend silhouettes |

## HUB Navigation

```
┌─────────────────────────────────────────┐
│  [LOGO]  SATOR eXe    [Game Selector ▼]  [User]  │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐    ┌─────────────┐    │
│  │   Q1        │    │     Q2      │    │
│  │  Tactical   │    │  Observer   │    │
│  │    Map      │    │    View     │    │
│  │             │    │             │    │
│  │  [Game      │    │  [Live      │    │
│  │   Specific  │    │   Feed]     │    │
│  │   Map]      │    │             │    │
│  └─────────────┘    └─────────────┘    │
│                                         │
│  ┌─────────────┐    ┌─────────────┐    │
│  │   Q3        │    │     Q4      │    │
│  │   Data      │    │  Settings   │    │
│  │  Rosarium   │    │   Ghost     │    │
│  │             │    │             │    │
│  │  [Analytics │    │  [Controls  │    │
│  │   Panels]   │    │   + Comms]  │    │
│  └─────────────┘    └─────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

## Game Selector Component

```
[Current: RadiantX ▼]
├─ RadiantX     [●]  Valorant
├─ CounterX     [○]  Counter-Strike  
├─ ApexX        [○]  Apex Legends
└─ [+ Add Game]
```

Switching games:
1. Preserves quaternary grid layout
2. Swaps accent color theme
3. Loads game-specific data schema
4. Updates map/agent libraries
5. Maintains user preferences per profile

## File Structure

```
sator-hub/
├── index.html              # Main HUB entry
├── system/                 # Universal layer
│   ├── css/
│   │   ├── core.css       # SATOR core styles
│   │   ├── quaternary.css # Grid system
│   │   └── glass.css      # Glass morphism
│   ├── js/
│   │   ├── hub.js         # Game switching
│   │   ├── grid.js        # Q1-Q4 manager
│   │   └── auth.js        # User system
│   └── components/
│       ├── GameSelector.js
│       ├── Quadrant.js
│       └── MorphingJunction.js
│
├── profiles/               # Game-specific layers
│   ├── radiantx/          # Valorant
│   │   ├── theme.css      # Red accent overrides
│   │   ├── maps/          # Haven, Bind, etc.
│   │   ├── agents/        # Jett, Sage, etc.
│   │   └── data-schema.js # Valorant KCRITR
│   │
│   ├── counterx/          # CS (future)
│   ├── apexX/             # Apex (future)
│   └── _template/         # New game boilerplate
│
└── assets/
    ├── fonts/
    ├── icons/
    └── shared/            # Cross-game visuals
```

## CSS Variable Cascade

```css
/* system/core.css — Universal */
:root {
  --sator-payne: #536878;
  --sator-cyan: #00f0ff;
  --sator-white: #f8f9fa;
  --sator-navy: #0a1628;
  --sator-vermilion: #e34234;
  --glass-opacity: 0.88;
  --glass-blur: 12px;
}

/* profiles/radiantx/theme.css — Override */
[data-profile="radiantx"] {
  --profile-accent: #ff4655;
  --profile-accent-glow: rgba(255, 70, 85, 0.4);
  --profile-bg-gradient: linear-gradient(180deg, #0a0a0f 0%, #1a0a1a 100%);
  --profile-map-tint: rgba(255, 70, 85, 0.1);
}

/* profiles/counterx/theme.css — Override */
[data-profile="counterx"] {
  --profile-accent: #f7931e;
  --profile-accent-glow: rgba(247, 147, 30, 0.4);
  --profile-bg-gradient: linear-gradient(180deg, #0a0f0a 0%, #1a1a0a 100%);
  --profile-map-tint: rgba(247, 147, 30, 0.1);
}
```

## Implementation Priority

1. **System Layer** — Quaternary grid, game selector, HUB shell
2. **RadiantX Profile** — Valorant theme, maps, agents
3. **Data Integration** — Axiom pipeline per profile
4. **Additional Games** — CounterX, ApexX templates

## Next Action

Build the HUB shell with:
- Game selector dropdown
- Quaternary grid container
- Profile CSS variable system
- RadiantX as first implemented profile
