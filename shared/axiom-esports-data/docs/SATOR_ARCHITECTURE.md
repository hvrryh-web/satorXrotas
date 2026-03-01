# SATOR_ARCHITECTURE.md — 5-Layer Visualization Specification

## Overview

The **SATOR Square** is a palindromic 5-layer visualization system for Valorant
match analysis. Each layer uses the SATOR square word palindrome as a mnemonic
for its function.

```
S A T O R
A R E P O
T E N E T
O P E R A
R O T A S
```

## Layer Specifications

### Layer 1: SATOR — Golden Halo System
- **Renderer:** D3.js SVG
- **Function:** Marks high-impact player moments
- **Events:** Plant, MVP, Hotstreak, Ace
- **Visual:** Animated golden halos, size scales with intensity (0.0–1.0)
- **Data source:** `sator_events` table
- **File:** `visualization/sator-square/layers/SatorLayer.tsx`

### Layer 2: OPERA — Fog of War
- **Renderer:** WebGL (Canvas)
- **Function:** Uncertainty visualization, partial observability
- **Visual:** Animated fog noise + audio-like uncertainty ripples
- **Shader:** `shaders/fog.frag` (GLSL fragment shader)
- **Data source:** Visibility mask array (Float32Array, per-tick)
- **File:** `visualization/sator-square/layers/OperaLayer.tsx`

### Layer 3: TENET — Area Control Grading
- **Renderer:** D3.js SVG
- **Function:** Zone control visualization with mutual exclusion
- **Visual:** Colored polygons per map zone (attack=blue, defense=red, contested=orange)
- **Grades:** A (complete control) → D (no control)
- **Data source:** Computed from ROTAS trail + round outcomes
- **File:** `visualization/sator-square/layers/TenetLayer.tsx`

### Layer 4: AREPO — Death Stains
- **Renderer:** D3.js SVG
- **Function:** Death location persistence, multikill markers, clutch crowns
- **Visual:** Colored circles (decay over rounds), clutch crown (♛) for 1vN wins
- **Persistence:** `persistRounds` parameter (default: 3 rounds)
- **Data source:** `arepo_markers` table
- **File:** `visualization/sator-square/layers/ArepoLayer.tsx`

### Layer 5: ROTAS — Rotation Trails
- **Renderer:** WebGL (Canvas) + motion dust particles
- **Function:** Player movement trails and lateral balance visualization
- **Visual:** Colored trails (attack=blue, defense=red) with dust particle head
- **LR Balance Wheel:** `directionLR` field (-1=left, 0=mid, +1=right)
- **Shader:** `shaders/dust.vert` (GLSL vertex shader for particles)
- **Data source:** `rotas_trails` table
- **File:** `visualization/sator-square/layers/RotasLayer.tsx`

## Rendering Stack

```
React Component Tree
├── SatorLayer (SVG — absolute positioned)
├── OperaLayer (WebGL Canvas — absolute positioned)
├── TenetLayer (SVG — absolute positioned)
├── ArepoLayer (SVG — absolute positioned)
└── RotasLayer (WebGL Canvas — absolute positioned)
     └── Map SVG background (public/map_svgs/)
```

All layers use `position: absolute; pointer-events: none` to stack without
interaction conflicts.

## Data Flow

```
useSpatialData(matchId, roundNumber)
  → /api/matches/{id}/rounds/{n}/sator-events → SatorLayer
  → /api/matches/{id}/rounds/{n}/arepo-markers → ArepoLayer
  → /api/matches/{id}/rounds/{n}/rotas-trails → RotasLayer
  → Visibility mask computed client-side from rotas data → OperaLayer
  → Zone control computed client-side from trail + kill data → TenetLayer
```

## Performance Notes

- D3.js layers (1, 3, 4): SVG, suitable for <200 elements
- WebGL layers (2, 5): Canvas, suitable for 1000+ particles/tick
- Target: 60 FPS at full match playback speed
