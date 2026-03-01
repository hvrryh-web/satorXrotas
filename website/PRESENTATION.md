# SATOR eXe Website Presentation Deck
## 25-Slide Design Specification

---

## SLIDE 1: SCAFFOLDING — Site Architecture
**Visual:** Clean wireframe diagram showing three-tier structure

```
┌─────────────────────────────────────────────────────────────┐
│                    SATOR eXe PLATFORM                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐ │
│   │  LANDING    │  →   │ LAUNCH PAD  │  →   │   PROFILE   │ │
│   │             │      │             │      │             │ │
│   │ SATOR Sphere│      │Constellation│      │  Quaternary │ │
│   │   Entry     │      │    Hub      │      │    Grid     │ │
│   └─────────────┘      └─────────────┘      └─────────────┘ │
│          │                    │                    │         │
│          └────────────────────┴────────────────────┘         │
│                      Unified Navigation                      │
└─────────────────────────────────────────────────────────────┘
```

**Components:**
- **Location:** Header logo (click to return)
- **Button:** "Enter" — center of landing sphere
- **Toggle:** None on this slide

**Design Notes:**
- Three-layer architecture: Entry → Hub → Application
- Consistent header across all pages
- Game profile system allows switching without leaving context

---

## SLIDE 2: TABLE OF CONTENTS
**Visual:** Grid of 6 sections with icons

| Section | Slides | Icon |
|---------|--------|------|
| **I. Landing Page** | 3-6 | 🌐 |
| **II. Launch Pad** | 7-12 | 🚀 |
| **III. Quaternary Grid** | 13-18 | ⬜ |
| **IV. Visual System** | 19-22 | 🎨 |
| **V. Interaction Design** | 23-24 | 👆 |
| **VI. Technical Specs** | 25 | ⚙️ |

**Components:**
- **Navigation:** Click section to jump
- **Progress:** Slide counter (2/25)

---

## SLIDE 3: LANDING PAGE — Overview
**Visual:** Full mockup with annotation callouts

```
┌─────────────────────────────────────────┐
│  [Starfield Background — 150 stars]     │
│                                         │
│         ┌─────────────────┐             │
│         │   SATOR eXe     │ ← Title    │
│         │  [cyan glow]    │             │
│         └─────────────────┘             │
│                                         │
│              [SPHERE]                   │
│         (animated rotation)             │
│                                         │
│         ┌─────────────────┐             │
│         │  CLICK TO ENTER │ ← Hint     │
│         │      [↓]        │   (pulse)  │
│         └─────────────────┘             │
│                                         │
└─────────────────────────────────────────┘
```

**Components:**
- **Text Box:** "Tactical Intelligence Infrastructure" — subtitle
- **Button:** None (whole page is clickable)
- **Toggle:** None

**Visual Effects:**
- Starfield: 150 stars with twinkle animation
- Sphere: 40s rotation, pauses on hover
- Glow: Electric Cyan text-shadow (0 0 40px)
- Warp transition on click (600ms zoom blur)

---

## SLIDE 4: LANDING PAGE — SATOR Sphere Detail
**Visual:** Isolated sphere with facet breakdown

```
                    [S]
                   [A][A]
                  [T][R][T]
                 [O][E][E][O]
                [R][P][N][P][R]
               ─────────────────  ← Equator
                [R][O][T][A][S]
                 (dimmer)
```

**Facet Colors:**
| Letter | Color | Hex | Glow |
|--------|-------|-----|------|
| S | Gold | #FFD700 | Drop shadow |
| A | Deep Blue | #1E3A5F | Light text |
| T | White | #FFFFFF | — |
| O | Cyan | #00D4FF | — |
| R | Red | #FF4655 | — |
| N | White | #FFFFFF | Center glow |

**Components:**
- **Button:** Each facet is clickable (future: layer details)
- **Toggle:** None

---

## SLIDE 5: LANDING PAGE — Animation Specs
**Visual:** Timeline diagrams

**Starfield Animation:**
```
Star Generation:
├── Count: 150 stars
├── Position: random(x,y)
├── Opacity: random(0-0.8)
├── Animation: twinkle 3-7s infinite
└── Delay: random(0-5s)
```

**Sphere Rotation:**
```
Default: rotate(360deg) / 40s linear infinite
Hover: animation-play-state: paused
Filter: drop-shadow(0 0 60px cyan) → (0 0 80px) on hover
```

**Warp Transition:**
```
0%   → scale(1), blur(0)
50%  → scale(1.5), blur(20px)
100% → scale(3), blur(60px), opacity(0)
Duration: 600ms → navigate to launchpad.html
```

---

## SLIDE 6: LANDING PAGE — Responsive States
**Visual:** Three device mockups side by side

| Desktop | Tablet | Mobile |
|---------|--------|--------|
| Sphere: 500px | Sphere: 400px | Sphere: 280px |
| Title: 5rem | Title: 4rem | Title: 2.5rem |
| Full starfield | Reduced stars | Minimal stars |
| All facets visible | All facets | Simplified |

**Breakpoint:** 640px

---

## SLIDE 7: LAUNCH PAD — Overview
**Visual:** Full constellation layout

```
                    ┌─────────┐
                   ╱    🚀    ╲
                  │  eXе Pad  │ ← Top
                   ╲___________╱
                         │
    ┌─────────┐     ┌────┴────┐     ┌─────────┐
   ╱    📊    ╲←────│   ZN    │────→╱    🎮    ╲
  │ Analytics │     │ Junction│     │ Tactical│
   ╲___________╱     └─────────┘     ╲___________╱
        │                                  │
        └──────────────┬───────────────────┘
                       │
              ┌────────┴────────┐
         ┌────┴────┐       ┌────┴────┐
        ╱    📰    ╲     ╱    📚    ╲
       │  eFanHUB   │   │  HelpHUB   │
        ╲___________╱     ╲___________╱
```

**Components:**
- **Buttons:** 5 service nodes (click to navigate)
- **Toggle:** None
- **Dock:** Quick access bar at bottom

---

## SLIDE 8: LAUNCH PAD — Service Nodes
**Visual:** Five cards with specifications

| Node | Position | Color | Icon | Destination |
|------|----------|-------|------|-------------|
| eXе | Top center | Cyan #00f0ff | 🚀 | landing.html |
| Analytics | Left | Vermilion #e34234 | 📊 | Coming Soon |
| Tactical | Right | Aurum #ffd700 | 🎮 | profiles/radiantx/ |
| eFanHUB | Bottom-left | Purple #9d4edd | 📰 | Coming Soon |
| Help HUB | Bottom-right | White #f8f9fa | 📚 | Coming Soon |

**Node Structure:**
```
┌─────────────────┐
│      Icon       │  ← 24px emoji
│   Subtitle      │  ← 10px uppercase
│   TITLE         │  ← 12px bold, colored
│ [hover expand]  │
└─────────────────┘
Width: 120px → 140px on hover
Background: glass morphism (88% opacity, blur 12px)
Border: 1px solid white/10% → colored on hover
```

---

## SLIDE 9: LAUNCH PAD — ZN Junction
**Visual:** Center element with glyph cycle

```
         ╭─────────────────╮
        ╱   ╭───────────╮   ╲
       │    │     J     │    │  ← Current glyph
       │    │  (glyph)  │    │
       │    ╰───────────╯    │
       │   ZN Junction       │  ← Label
        ╲___________________╱
              (pulse)
```

**Glyph Cycle:**
```
J → ? → j → ! → i → ∞ → 8 → (repeat)
     │                    │
     └──── 22.4s cycle ───┘
     
Transition: 150ms fade
Focus mode: 11.2s cycle (2x speed)
```

**Components:**
- **Text Box:** "ZN Junction" label
- **Button:** None (display only)
- **Toggle:** None

---

## SLIDE 10: LAUNCH PAD — Constellation Lines
**Visual:** SVG path diagram with animation

**Connection Lines:**
```svg
Center to eXе:      stroke: cyan/20%, animated
Center to Analytics: stroke: cyan/20%, animated  
Center to Tactical:  stroke: cyan/20%, animated
Center to eFan:      stroke: cyan/10%, static
Center to Help:      stroke: cyan/10%, static
Cross (Analytics-Tactical): stroke: cyan/5%, static
```

**Animation:**
```css
stroke-dasharray: 8 4;
animation: dataFlow 2s linear infinite;

@keyframes dataFlow {
  to { stroke-dashoffset: -24; }
}
```

**Components:**
- **Toggle:** Lines brighten on node hover

---

## SLIDE 11: LAUNCH PAD — Quick Access Dock
**Visual:** Bottom bar with items

```
┌─────────────────────────────────────────────────────────────┐
│  QUICK ACCESS  │  [🎮 Tactical] [📊 Analytics] [📚 Help]  │  Press 1-5  │
└─────────────────────────────────────────────────────────────┘
```

**Dock Items:**
- Recent services (last 3 accessed)
- Click to navigate
- Keyboard shortcuts: 1-5

**Components:**
- **Buttons:** Dock items (clickable)
- **Text Box:** "Press 1-5" hint

---

## SLIDE 12: LAUNCH PAD — Responsive Grid
**Visual:** Position adjustments per breakpoint

| Element | Desktop | Tablet | Mobile |
|---------|---------|--------|--------|
| eXе | Top center | Top center | Top center |
| Analytics | Left 8% | Left 5% | Left 5% |
| Tactical | Right 8% | Right 5% | Right 5% |
| eFan | Bottom-left 15% | Bottom-left 10% | Bottom-left 5% |
| Help | Bottom-right 15% | Bottom-right 10% | Bottom-right 5% |
| ZN | Center | Center | Center |

**Node scaling:** 120px → 90px on mobile

---

## SLIDE 13: QUATERNARY GRID — Overview
**Visual:** 2×2 grid layout

```
┌─────────────────────┬─────────────────────┐
│                     │                     │
│   Q1: TACTICAL      │   Q2: OBSERVER      │
│       MAP           │       VIEW          │
│                     │                     │
│  [Map placeholder]  │  [Live feed]        │
│  [Map selector]     │  [LIVE badge]       │
│                     │                     │
├─────────────────────┼─────────────────────┤
│                     │                     │
│   Q3: DATA          │   Q4: SETTINGS      │
│    ROSARIUM         │     GHOST           │
│                     │                     │
│  [Stats grid]       │  [Toggle list]      │
│  [4 cards]          │  [3 settings]       │
│                     │                     │
└─────────────────────┴─────────────────────┘
```

**Grid Specs:**
- Gap: 1px (divider lines)
- Background: #2a2a3a (gap color)
- Quadrant: rgba(20,20,31,0.98)

---

## SLIDE 14: Q1 — Tactical Map
**Visual:** Detailed quadrant mockup

```
┌────────────────────────────────────┐
│  🗺️  Q1 — TACTICAL MAP    [⚙️][⛶] │  ← Header
├────────────────────────────────────┤
│                                    │
│    ┌────────────────────────┐      │
│    │                        │      │
│    │     [MAP PLACEHOLDER]  │      │
│    │                        │      │
│    │   Select a map to view │      │
│    │    tactical overlay    │      │
│    │                        │      │
│    └────────────────────────┘      │
│                                    │
│    [Haven] [Bind] [Split] [Ascent] │  ← Map selector
│      ↑ active                      │
└────────────────────────────────────┘
```

**Components:**
- **Buttons:** Map selector tabs, Settings (⚙️), Fullscreen (⛶)
- **Text Box:** Placeholder instructions
- **Toggle:** None

**Colors:**
- Header icon: Cyan background
- Active map: Red background (#ff4655/20%)

---

## SLIDE 15: Q2 — Observer View
**Visual:** Video feed quadrant

```
┌────────────────────────────────────┐
│  📹  Q2 — OBSERVER VIEW   [⏸][⛶] │
├────────────────────────────────────┤
│                                    │
│  ┌────────────────────────────┐    │
│  │  ● LIVE                    │    │  ← Badge
│  │                            │    │
│  │         🎮                 │    │
│  │                            │    │
│  │     Match Feed             │    │
│  │   SEN vs FNC — Haven       │    │
│  │                            │    │
│  └────────────────────────────┘    │
│                                    │
└────────────────────────────────────┘
```

**Components:**
- **Buttons:** Pause (⏸️), Fullscreen (⛶)
- **Badge:** LIVE indicator with pulsing dot
- **Text Box:** Match info

**Live Badge:**
```css
Background: rgba(255,70,85,0.2)
Border: 1px solid rgba(255,70,85,0.4)
Dot: 6px, #ff4655, pulse animation 1.5s
```

---

## SLIDE 16: Q3 — Data Rosarium
**Visual:** Stats cards grid

```
┌────────────────────────────────────┐
│  📊  Q3 — DATA ROSARIUM   [📅][⛶] │
├────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐    │
│  │ Matches    │  │ Avg ACS    │    │
│  │ ─────────  │  │ ─────────  │    │
│  │   12.4K    │  │   218.5    │    │
│  │  +8.3% ↑   │  │  +3.2% ↑   │    │
│  └────────────┘  └────────────┘    │
│  ┌────────────┐  ┌────────────┐    │
│  │ Win Rate   │  │ Headshot % │    │
│  │ ─────────  │  │ ─────────  │    │
│  │   54.2%    │  │   24.8%    │    │
│  │  -1.1% ↓   │  │  +2.4% ↑   │    │
│  └────────────┘  └────────────┘    │
└────────────────────────────────────┘
```

**Stat Card:**
- Label: 10px uppercase, gray
- Value: 24px mono, red (#ff4655)
- Change: 12px, green/red

**Components:**
- **Buttons:** Calendar (📅), Fullscreen (⛶)
- **Text Boxes:** Stat labels and values

---

## SLIDE 17: Q4 — Settings Ghost
**Visual:** Toggle list quadrant

```
┌────────────────────────────────────┐
│  ⚙️  Q4 — SETTINGS GHOST  [↺][⛶] │
├────────────────────────────────────┤
│                                    │
│  ┌────────────────────────────┐    │
│  │  🔔  Live Notifications    │ [●]│  ← Toggle ON
│  │      Alert on match start  │    │
│  └────────────────────────────┘    │
│  ┌────────────────────────────┐    │
│  │  📊  Auto-Update Data      │ [●]│  ← Toggle ON
│  │      Refresh every 30s     │    │
│  └────────────────────────────┘    │
│  ┌────────────────────────────┐    │
│  │  👻  Ghost Mode            │ [○]│  ← Toggle OFF
│  │      Fade inactive panels  │    │
│  └────────────────────────────┘    │
│                                    │
└────────────────────────────────────┘
```

**Toggle Component:**
```
Width: 44px, Height: 24px
Background OFF: #2a2a3a
Background ON: #ff4655
Thumb: 20px circle, white
Animation: 200ms slide
```

**Components:**
- **Buttons:** Reset (↺), Fullscreen (⛶)
- **Toggles:** 3 settings (click to toggle)

---

## SLIDE 18: QUATERNARY GRID — Responsive
**Visual:** Breakpoint transformations

**Desktop (≥1024px):**
```
┌────────┬────────┐
│   Q1   │   Q2   │
├────────┼────────┤
│   Q3   │   Q4   │
└────────┴────────┘
2×2 grid
```

**Mobile (<1024px):**
```
┌────────┐
│   Q1   │
├────────┤
│   Q2   │
├────────┤
│   Q3   │
├────────┤
│   Q4   │
└────────┘
1×4 stacked
```

---

## SLIDE 19: VISUAL SYSTEM — Color Palette
**Visual:** Color swatches with usage

### SATOR Core (Universal)
| Color | Hex | Usage |
|-------|-----|-------|
| Deep Navy | #0a1628 | Background |
| Navy Light | #141e33 | Cards |
| Electric Cyan | #00f0ff | Primary accent, glows |
| Porcelain White | #f8f9fa | Text |

### Service Nodes
| Node | Color | Hex |
|------|-------|-----|
| eXе | Cyan | #00f0ff |
| Analytics | Vermilion | #e34234 |
| Tactical | Aurum | #ffd700 |
| eFan | Purple | #9d4edd |
| Help | White | #f8f9fa |

### RadiantX Override
| Element | Color | Hex |
|---------|-------|-----|
| Accent | Valorant Red | #ff4655 |
| Live indicator | Red | #ff4655 |
| Win rate up | Green | #00ff88 |

---

## SLIDE 20: VISUAL SYSTEM — Typography
**Visual:** Type scale specimen

**Font Families:**
- Primary: Inter (UI, headers)
- Mono: JetBrains Mono (data, stats)

**Scale:**
| Level | Size | Weight | Usage |
|-------|------|--------|-------|
| Display | 48-80px | 700 | Landing title |
| H1 | 32px | 700 | Page titles |
| H2 | 24px | 600 | Section headers |
| Body | 16px | 400 | Paragraphs |
| Caption | 12px | 500 | Labels |
| Data | 14-24px | 600 | Stats (mono) |

**Text Treatments:**
- Landing title: -0.02em letter-spacing
- Subtitles: +0.05em, uppercase
- Stats: tabular numbers

---

## SLIDE 21: VISUAL SYSTEM — Glass Morphism
**Visual:** Layer diagram

```
┌─────────────────────────────┐
│     Content Layer           │  ← Text, icons
├─────────────────────────────┤
│  Background: rgba(10,22,40, │
│             0.88)           │  ← 88% opacity
├─────────────────────────────┤
│  Backdrop-filter: blur(12px)│  ← Glass effect
├─────────────────────────────┤
│  Border: 1px solid white/10%│  ← Subtle edge
├─────────────────────────────┤
│  Box-shadow: 0 8px 32px     │  ← Depth
│             rgba(0,0,0,0.3) │
└─────────────────────────────┘
```

**Hover State:**
- Border: colored (node-specific)
- Shadow: 0 0 30px colored-glow

---

## SLIDE 22: VISUAL SYSTEM — Effects & Animation
**Visual:** Animation timeline diagrams

**Standard Transitions:**
| Type | Duration | Easing |
|------|----------|--------|
| Fast | 150ms | ease |
| Base | 250ms | ease |
| Slow | 400ms | ease |
| Bounce | 500ms | cubic-bezier(0.34, 1.56, 0.64, 1) |

**Special Animations:**
- Sphere rotation: 40s linear infinite
- Star twinkle: 3-7s ease-in-out infinite
- ZN morph: 3.2s per glyph, 22.4s cycle
- Data flow: 2s linear infinite
- Live pulse: 1.5s ease-in-out infinite
- Warp zoom: 600ms ease-out

---

## SLIDE 23: INTERACTION — Click Targets
**Visual:** Heat map overlay on mockup

**Landing Page:**
- Full page click → Launch Pad
- Sphere hover → Pause rotation

**Launch Pad:**
| Element | Action | Destination |
|---------|--------|-------------|
| eXе node | Click | landing.html |
| Analytics node | Click | Alert (soon) |
| Tactical node | Click | radiantx/index.html |
| eFan node | Click | Alert (soon) |
| Help node | Click | Alert (soon) |
| Dock item | Click | Same as node |
| Logo | Click | landing.html |

**Quaternary Grid:**
| Element | Action |
|---------|--------|
| Map selector | Switch map |
| Settings (⚙️) | Open settings |
| Fullscreen (⛶) | Expand quadrant |
| Toggle | ON/OFF |
| Back button | launchpad.html |

---

## SLIDE 24: INTERACTION — Keyboard Shortcuts
**Visual:** Keyboard diagram with highlighted keys

**Launch Pad:**
| Key | Action |
|-----|--------|
| 1 | Go to eXе (landing) |
| 2 | Open Analytics |
| 3 | Open Tactical (RadiantX) |
| 4 | Open eFanHUB |
| 5 | Open Help HUB |

**Global:**
| Key | Action |
|-----|--------|
| Esc | Back / Close |
| F | Fullscreen current quadrant |

---

## SLIDE 25: TECHNICAL — Implementation Stack
**Visual:** Tech stack icons

**Core Technologies:**
- HTML5 (semantic structure)
- CSS3 (custom properties, grid, flex)
- Vanilla JavaScript (no framework)

**External Resources:**
- Tailwind CSS (CDN)
- Google Fonts: Inter, JetBrains Mono

**File Structure:**
```
radiantx-static/
├── landing.html
├── launchpad.html
├── system/
│   ├── core.css
│   └── js/
│       └── (inline for now)
└── profiles/
    └── radiantx/
        ├── index.html
        └── theme.css
```

**Performance Targets:**
- First paint: <1s
- Interactive: <2s
- Bundle size: <100KB (excluding fonts)

---

## END OF PRESENTATION

**Next Steps:**
1. Review slides with stakeholders
2. Export to presentation format (PDF/PPTX)
3. Create interactive prototype
4. User testing
5. Development sprint

**Contact:** SATOR eXe Design Team
