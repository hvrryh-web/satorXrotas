# SATOR Sphere Design Documentation
## Triangle Embedding Foil Pattern on Spherical Surface

---

## Concept Overview

The SATOR Sphere transforms the 5×5 palindrome square into a 3D geodesic sphere using **diagonal-split triangular facets**. Each original square tile becomes two triangular half-tiles, creating a tessellated surface that wraps around the sphere.

---

## The 5½ Tile Structure

### Original SATOR Square
```
S A T O R     Row 1: 1 tile
A R E P O     Row 2: 2 tiles
T E N E T     Row 3: 3 tiles
O P E R A     Row 4: 4 tiles
R O T A S     Row 5: 5 tiles
```

### Spherical Mapping

**Upper Hemisphere (SATOR):**
```
        [S]                    ← Pole (1 triangle)
       [A][A]                  ← Row 2 (2 triangles)
      [T][R][T]                ← Row 3 (3 triangles)
     [O][E][E][O]              ← Row 4 (4 triangles)
    [R][P][N][P][R]            ← Equator (5 triangles)
```

**Lower Hemisphere (ROTAS):**
```
    [R][O][T][A][S]            ← Equator (5 triangles)
     [O][P][E][R][A]           ← Row 7 (5 triangles)
      [T][E][N][E][T]          ← Row 8 (4 triangles)
       [A][R][E][P][O]         ← Row 9 (3 triangles)
        [S]                    ← Pole (1 triangle)
```

**Total: 50 triangular facets** (25 squares × 2 diagonal splits)

---

## The Diagonal Split Pattern

Each square tile is split into two triangles:

```
Original Square:        Diagonal Split A:       Diagonal Split B:
┌─────────┐            ┌─────────┐             ┌─────────┐
│         │            │╲        │             │        ╱│
│    S    │     →      │  ╲  S   │      or     │   S  ╱  │
│         │            │    ╲    │             │    ╱    │
└─────────┘            └──────╲──┘             └──╱──────┘
                       Triangle 1: TL-BR        Triangle 1: TR-BL
                       Triangle 2: TR-BL        Triangle 2: TL-BR
```

**Alternating Pattern:**
- Odd rows: Type A diagonal (top-left to bottom-right)
- Even rows: Type B diagonal (top-right to bottom-left)
- This creates a continuous mesh without gaps

---

## How Images 2 & 3 Inform the Design

### Image 2: "188,743,680 Symmetries"
**Key Insight:** The cube-to-sphere transformation

**Application to SATOR Sphere:**
- The flat SATOR square "unfolds" onto the sphere like a cube projection
- Each face of the cube corresponds to a quadrant of the SATOR pattern
- The symmetries suggest multiple valid rotations where SATOR aligns

**Design Element:**
```
Cube Projection → Spherical Mapping:

    ┌─────┐
   ╱     ╱│
  ┌─────┐ │     →     Spherical SATOR
  │     │╱            with 5-fold symmetry
  └─────┘             at poles
```

### Image 3: Triangular Mesh & Flow Lines
**Part (a): Triangular Mesh Pattern**
- Shows how the diagonal splits create a tessellated surface
- The spiral embedding suggests how letters flow from pole to equator
- Each triangle connects to neighbors, forming a continuous surface

**Part (b): Sphere with Flow Lines**
- Trajectories wrapping around the sphere
- Represents data flow, player movement, or energy
- Lines follow the triangular facet edges

**Combined Application:**
```
Triangular Facets + Flow Lines:

    ╭───────────────╮
   ╱  ▲    ▲    ▲   ╲      ▲ = Facet normal
  │  ╱ ╲  ╱ ╲  ╱ ╲   │     ╱╲ = Triangle
  │ ●───●───●───●   │     ● = Flow node
  │  ╲ ╱  ╲ ╱  ╲ ╱   │     ─ = Flow path
   ╲  ▼    ▼    ▼   ╱
    ╰───────────────╯
```

---

## The Foil Pattern Concept

### What is "Foil Embedding"?

A **foil** in mathematics is a surface that intersects itself or another surface. In design, it creates:
- **Depth illusions:** Multiple layers appearing to pass through each other
- **Moire patterns:** Interference patterns from overlapping grids
- **Kinetic effects:** Patterns that shift as viewing angle changes

### SATOR Sphere Foil Application

**Layer 1: Base Facets (Matte)**
- SATOR side: Embossed letters, matte finish
- ROTAS side: Recessed letters, glossy finish

**Layer 2: Flow Lines (Translucent)**
- Animated lines tracing spiral paths
- Follow the triangular mesh edges
- Color-coded by layer (S=gold, A=blue, etc.)

**Layer 3: Glow Overlay (Additive)**
- Center glow at TENET positions
- Pulsing emission from active facets
- Creates "breathing" effect

**The Foil Effect:**
```
Cross-section view:

    ╱╲    ╱╲    ╱╲
   ╱  ╲  ╱  ╲  ╱  ╲     ← Layer 1: Facets (solid)
  ╱────╲╱────╲╱────╲
   ════════════════      ← Layer 2: Flow lines (translucent)
    · · · · · · · ·      ← Layer 3: Glow particles (additive)
```

---

## Visual Design Specifications

### Color Coding

| Letter | Primary | Dark Variant | Meaning |
|--------|---------|--------------|---------|
| S | #FFD700 (Gold) | #B8860B | Sower/Genesis |
| A | #1E3A5F (Deep Blue) | #0F1D2F | Arepo/Hidden |
| T | #FFFFFF (White) | #CCCCCC | Tenet/Axis |
| O | #00D4FF (Cyan) | #0099BB | Opera/Works |
| R | #FF4655 (Red) | #CC3844 | Rotas/Cycle |
| N | #FFFFFF (White) | #CCCCCC | Center/Heart |
| P | #00D4FF (Cyan) | #0099BB | Opera/Works |
| E | #1E3A5F (Deep Blue) | #0F1D2F | Connection |

### Typography

- **Facet Letters:** JetBrains Mono, 14px, bold
- **Dark backgrounds (A, E, N):** White text
- **Light backgrounds (S, T, O, R, P):** Black text

### Animations

**1. Idle Rotation:**
- Speed: 1 RPM (0.005 rad/frame)
- Axis: Y-axis (vertical)
- Easing: Linear

**2. Hover State:**
- Facet scale: 1.1x
- Emissive glow: +0x444444
- Tooltip: Fade in 300ms

**3. Click/Flip:**
- Duration: 800ms
- Rotation: 180° on X-axis
- Easing: Cubic-bezier(0.4, 0, 0.2, 1)

**4. Flow Lines:**
- Speed: 3s per cycle
- Pattern: Dash array 10-5
- Direction: SATOR pole → ROTAS pole

---

## Implementation Files

| File | Technology | Purpose |
|------|------------|---------|
| `sator-sphere-css.html` | CSS/SVG | Lightweight, fast loading, mobile-friendly |
| `sator-sphere-threejs.html` | Three.js | Full 3D interactivity, WebGL effects |

### When to Use Each

**CSS/SVG Version:**
- Mobile devices
- Low-bandwidth connections
- Static display/embed
- Fallback for no-WebGL

**Three.js Version:**
- Desktop experiences
- Interactive dashboards
- Hero sections
- Product showcases

---

## Next Steps

1. **Review both prototypes** in your browser
2. **Select preferred interactions** (hover, click, auto-rotate)
3. **Refine color palette** if needed
4. **Integrate with RadiantX dashboard** data
5. **Add match data visualization** (flow lines = player paths)

---

*Documentation created: February 26, 2026*
