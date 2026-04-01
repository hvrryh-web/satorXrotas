# eSports-EXE Visual Specification Document v3
## Pixel-Perfect Design System

---

## 1. LAYOUT GRID SYSTEM

### Primary Grid: 12-Column
```
| Margin | Col 1 | Col 2 | Col 3 | ... | Col 12 | Margin |
|  24px  |  72px |  72px |  72px | ... |  72px  |  24px  |

Total Width: 1200px (max)
Gutter: 24px
Column: 72px
```

### Breakpoints
| Name | Width | Behavior |
|------|-------|----------|
| Mobile | < 640px | Single column, stacked |
| Tablet | 640-1024px | 2-column |
| Desktop | > 1024px | Full 12-column |

---

## 2. SPACING SCALE (8px Base)

| Token | Value | Usage |
|-------|-------|-------|
| space-1 | 4px | Tight internal padding |
| space-2 | 8px | Icon padding |
| space-3 | 12px | Small component gap |
| space-4 | 16px | Default padding |
| space-5 | 24px | Section gap |
| space-6 | 32px | Large section gap |
| space-7 | 48px | Hero section padding |
| space-8 | 64px | Major section breaks |

---

## 3. TYPOGRAPHY

### Font Stack
```css
--font-heading: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
--font-data: 'JetBrains Mono', monospace; /* Tabular numbers */
```

### Type Scale
| Style | Size | Weight | Line Height | Letter Spacing | Usage |
|-------|------|--------|-------------|----------------|-------|
| Hero | 48px | 800 | 1.1 | -0.02em | Main headlines |
| H1 | 36px | 700 | 1.2 | -0.01em | Page titles |
| H2 | 28px | 600 | 1.3 | 0 | Section headers |
| H3 | 22px | 600 | 1.4 | 0 | Card titles |
| H4 | 18px | 600 | 1.4 | 0 | Subsection |
| Body | 16px | 400 | 1.6 | 0 | Paragraphs |
| Small | 14px | 400 | 1.5 | 0 | Secondary text |
| Caption | 12px | 500 | 1.4 | 0.02em | Labels, badges |
| Data | 16px | 500 | 1.0 | 0.02em | Stats, numbers |

---

## 4. COLOR SYSTEM (Strict Usage)

### Primary Palette
| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| **bg-primary** | `#0A0A0A` | 10,10,10 | Main background |
| **bg-secondary** | `#141414` | 20,20,20 | Elevated surfaces |
| **bg-tertiary** | `#1A1A1A` | 26,26,26 | Cards, panels |
| **bg-hover** | `#262626` | 38,38,38 | Hover states |

### Accent Colors (RESTRICTED)
| Token | Hex | Usage | Constraint |
|-------|-----|-------|------------|
| **accent-teal** | `#14B8A6` | ROTAS/SATOR data highlights | ONLY for stats, ratings, success states |
| **accent-orange** | `#F97316` | OPERA/AREPO CTAs | ONLY for primary buttons, critical actions |
| **accent-red** | `#FF4655` | Errors, live indicators, Valorant brand | ONLY for LIVE badge, error states |
| **accent-blue** | `#3B82F6` | CS2 brand, team colors | ONLY for CS2-specific elements |

### Neutral Colors
| Token | Hex | Usage |
|-------|-----|-------|
| **text-primary** | `#F8FAFC` | Headlines, primary text |
| **text-secondary** | `#94A3B8` | Descriptions, labels |
| **text-muted** | `#64748B` | Disabled, hints |
| **border-default** | `#2A2A2A` | Card borders |
| **border-active** | `#14B8A6` | Active state borders |

### Color Usage Rules (MUST FOLLOW)
```
✓ ACCENT-TEAL: Player ratings, stat values, WIN badges, active HUB indicator
✓ ACCENT-ORANGE: Primary CTA buttons only ("Compare", "Follow", "View")
✗ NEVER: Orange for stats, Orange for headlines, Orange for backgrounds
✗ NEVER: Teal for buttons, Teal for backgrounds
```

---

## 5. BORDER RADIUS (Strict)

| Token | Value | Usage |
|-------|-------|-------|
| **radius-none** | 0px | Sharp corners (preferred) |
| **radius-sm** | 2px | Data tables, stat cards |
| **radius-md** | 4px | Interactive cards (MAX allowed) |
| **radius-lg** | 8px | Modals, overlays |

**RULE:** Default to 0px. Maximum 4px for interactive elements. NO exceptions.

---

## 6. SHADOWS & DEPTH

| Token | Value | Usage |
|-------|-------|-------|
| **shadow-sm** | `0 1px 2px rgba(0,0,0,0.3)` | Subtle elevation |
| **shadow-md** | `0 4px 12px rgba(0,0,0,0.4)` | Cards |
| **shadow-lg** | `0 8px 32px rgba(0,0,0,0.5)` | Modals, dropdowns |
| **shadow-glow-teal** | `0 0 20px rgba(20,184,166,0.15)` | Active/focus states |
| **shadow-glow-orange** | `0 0 20px rgba(249,115,22,0.15)` | CTA hover |

### Vignette Masks (MANDATORY)
```css
/* Top vignette for headers */
.vignette-top {
  background: linear-gradient(
    to bottom,
    rgba(10,10,10,0.8) 0%,
    transparent 100%
  );
}

/* Bottom vignette for cards */
.vignette-bottom {
  background: linear-gradient(
    to top,
    rgba(10,10,10,0.9) 0%,
    transparent 60%
  );
}

/* Full card vignette for game tiles */
.vignette-card {
  background: radial-gradient(
    ellipse at center,
    transparent 0%,
    rgba(10,10,10,0.7) 100%
  );
}
```

---

## 7. COMPONENT SPECIFICATIONS

### 7.1 HUB Quadrant Card (CRITICAL)
```
┌─────────────────────────────┐
│                             │
│      [ICON 48×48]           │ ← Centered icon
│                             │
│        ROTAS                │ ← H2, text-primary
│      Stats & Data           │ ← Body, text-secondary
│                             │
│  [Live: 3] [Upcoming: 12]   │ ← Data tags
│                             │
├─────────────────────────────┤
│  View Stats →               │ ← Link, accent-teal
└─────────────────────────────┘

Dimensions:
- Width: 280px (desktop)
- Height: 320px (fixed)
- Padding: 24px
- Border: 1px solid border-default
- Radius: 0px
- Background: bg-tertiary

Hover:
- Border: 1px solid accent-teal
- Shadow: shadow-glow-teal
- Transform: translateY(-4px)
```

### 7.2 Game Selection Tile
```
┌─────────────────────────────┐
│  ╔═══════════════════════╗  │ ← Vignette overlay
│  ║  [VALORANT LOGO]      ║  │
│  ║                       ║  │
│  ║  [LIVE]    3 Matches  ║  │ ← Badge + data
│  ╚═══════════════════════╝  │
│      VALORANT               │ ← H3, text-primary
│      Tactical FPS           │ ← Small, text-muted
└─────────────────────────────┘

Dimensions:
- Width: 360px
- Height: 200px
- Image: Full cover with vignette-card
- Radius: 0px
- Badge: accent-red, positioned top-left
```

### 7.3 Data Table (Leaderboard)
```
Header Row:
┌─────────────────────────────────────────────────────────────┐
│ #  │ Player          │ Team │ Role │ K/D  │ ADR  │ Rating │
├────┼─────────────────┼──────┼──────┼──────┼──────┼────────┤
│ 1  │ ○ TenZ      🇨🇦 │ SEN  │ DUEL │ 1.45 │ 185  │ 1.35   │
│ 2  │ ○ aspas     🇧🇷 │ LEV  │ DUEL │ 1.42 │ 179  │ 1.32   │
└────┴─────────────────┴──────┴──────┴──────┴──────┴────────┘

Specifications:
- Row height: 56px
- Padding: 16px horizontal
- Font: font-data for numbers
- Border-bottom: 1px solid border-default
- Hover: bg-hover
- Rating: accent-teal, font-weight 600
```

### 7.4 Stat Card (Player Profile)
```
┌─────────────┐
│             │
│    1.35     │ ← Data, 32px, accent-teal
│             │
│   Rating    │ ← Caption, text-secondary
│             │
└─────────────┘

Dimensions:
- Width: 120px
- Height: 120px
- Background: bg-tertiary
- Border: 1px solid border-default
- Radius: 0px
- Gap between cards: 16px
```

---

## 8. TENET PORTAL LAYOUT (EXACT)

```
┌─────────────────────────────────────────────────────────────┐
│  eSports-EXE                                    [Search]    │ ← 64px height
├─────────────────────────────────────────────────────────────┤
│                                                             │
│          The Esports Analytics Platform                     │ ← Hero: 48px
│     Unified stats for tactical FPS.                        │ ← Body: 16px
│                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │   [ROTAS]     │  │   [SATOR]     │  │               │   │ ← 4 tiles
│  │               │  │               │  │               │   │    2×2 grid
│  └───────────────┘  └───────────────┘  │               │   │
│  ┌───────────────┐  ┌───────────────┐  │               │   │
│  │   [OPERA]     │  │   [AREPO]     │  │               │   │
│  │               │  │               │  │               │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │    [Valorant]       │  │      [CS2]          │          │ ← Game tiles
│  │                     │  │                     │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘

RULES:
- NO feature cards below game tiles
- NO scrolling on this page
- ALL content fits in 100vh
- 4 HUB tiles in 2×2 grid
- 2 Game tiles side by side
```

---

## 9. INTERACTION STATES

### Hover States
```css
/* Cards */
.card:hover {
  border-color: var(--accent-teal);
  box-shadow: var(--shadow-glow-teal);
  transform: translateY(-4px);
  transition: all 0.2s ease;
}

/* Buttons */
.btn-primary:hover {
  background: var(--accent-orange);
  box-shadow: var(--shadow-glow-orange);
}

/* Table rows */
.tr:hover {
  background: var(--bg-hover);
}
```

### Focus States (Accessibility)
```css
:focus-visible {
  outline: 2px solid var(--accent-teal);
  outline-offset: 2px;
}
```

### Active States
```css
.btn-primary:active {
  transform: translateY(0);
  box-shadow: none;
}
```

---

## 10. ANIMATION SPECIFICATIONS

| Animation | Duration | Easing | Usage |
|-----------|----------|--------|-------|
| Hover lift | 200ms | ease-out | Card hover |
| Fade in | 300ms | ease-in-out | Page transitions |
| Slide up | 400ms | cubic-bezier(0.4, 0, 0.2, 1) | Modals |
| Skeleton shimmer | 1.5s | linear | Loading states |
| Data update | 300ms | ease | Live stats |

---

## 11. VALIDATION CHECKLIST

Before submitting wireframes, verify:

- [ ] No border radius > 4px anywhere
- [ ] Exactly 4 HUB tiles on TENET portal
- [ ] Zero feature cards (the 4×2 row eliminated)
- [ ] accent-orange ONLY on primary CTAs
- [ ] accent-teal ONLY on data/stats/ratings
- [ ] Vignette masks applied to game tiles
- [ ] All numbers use font-data (monospace)
- [ ] Sharp corners (0px radius) on data tables
- [ ] No scroll on TENET portal (100vh max)
- [ ] Quadrant modularity present (2×2 HUB grid)

---

Document Version: 3.0.0
Last Updated: 2026-03-31
Status: MANDATORY for all wireframe implementations
