# Web Design Components Table
## Analysis of StandardGT, Cirridae, and Top Awarded Designs

---

## COMPONENT CATEGORIES

### 1. LAYOUT SYSTEMS

| Component | StandardGT | Cirridae | Awwwards SOTD | Recommendation |
|-----------|------------|----------|---------------|----------------|
| **Grid System** | 12-column flex | CSS Grid + Flex | Custom asymmetric | Use 12-col for consistency |
| **Breakpoints** | 4 breakpoints | 3 breakpoints | Fluid/animated | 4 breakpoints (mobile-first) |
| **Container** | Max-width 1200px | Full-bleed optional | Variable | 1200px max, centered |
| **Spacing** | 8px base | 4px base | Variable | 8px base scale |
| **Responsive** | Mobile-first | Desktop-first | Contextual | Mobile-first mandatory |

---

### 2. TYPOGRAPHY

| Element | StandardGT | Cirridae | Awwwards SOTD | Recommendation |
|---------|------------|----------|---------------|----------------|
| **Primary Font** | Inter | System UI | Custom/Variable | Inter (proven, readable) |
| **Mono Font** | JetBrains Mono | Fira Code | Custom | JetBrains Mono (tabular) |
| **Type Scale** | Major Third | Perfect Fourth | Custom | Major Third (1.25) |
| **Line Height** | 1.5-1.6 | 1.4-1.5 | Variable | 1.6 body, 1.2 headings |
| **Font Loading** | swap | optional | critical | swap (performance) |

---

### 3. COLOR SYSTEMS

| Aspect | StandardGT | Cirridae | Awwwards SOTD | Recommendation |
|--------|------------|----------|---------------|----------------|
| **Primary** | Blue #3B82F6 | Purple #8B5CF6 | Brand-specific | Teal #14B8A6 |
| **Secondary** | Gray slate | Indigo | Complementary | Orange #F97316 |
| **Dark Mode** | Built-in | Manual toggle | Auto-detect | Default dark |
| **Color Count** | 12 colors | 8 colors | 2-4 colors | Strict 5-color palette |
| **Contrast Ratio** | AAA | AA | Variable | AAA (accessibility) |

---

### 4. BORDERS & RADIUS

| Element | StandardGT | Cirridae | Awwwards SOTD | Our Requirement |
|---------|------------|----------|---------------|-----------------|
| **Card Radius** | 8px | 4px | 0-16px | **0px (sharp)** |
| **Button Radius** | 6px | 4px | 0-50px | **0px or 4px max** |
| **Input Radius** | 4px | 2px | 0-8px | **0px** |
| **Border Width** | 1px | 1px | 0-2px | 1px |
| **Border Color** | Gray-200 | Gray-300 | Variable | #2A2A2A |

**Key Finding:** Top awarded sites use **0px radius** for premium feel (Apple, VLR.gg)

---

### 5. SHADOWS & DEPTH

| Type | StandardGT | Cirridae | Awwwards SOTD | Recommendation |
|------|------------|----------|---------------|----------------|
| **Card Shadow** | sm/md/lg | Flat or subtle | Layered/animated | md: `0 4px 12px rgba(0,0,0,0.4)` |
| **Hover Shadow** | Increased | Glow effects | Transform + shadow | Glow: `0 0 20px rgba(20,184,166,0.15)` |
| **Modal Shadow** | xl | lg | Custom | lg: `0 8px 32px rgba(0,0,0,0.5)` |
| **Vignette** | None | None | Common | **Mandatory radial gradient** |

---

### 6. BUTTONS

| Variant | StandardGT | Cirridae | Awwwards SOTD | Recommendation |
|---------|------------|----------|---------------|----------------|
| **Primary** | Filled, rounded | Filled, sharp | Variable | Filled, sharp, teal |
| **Secondary** | Outline | Ghost | Variable | Ghost, border only |
| **Danger** | Red filled | Red outline | Variable | Red outline |
| **Disabled** | Opacity 50% | Grayscale | Variable | Opacity 50% |
| **Loading** | Spinner | Skeleton | Animation | Spinner |

---

### 7. CARDS

| Feature | StandardGT | Cirridae | Awwwards SOTD | Recommendation |
|---------|------------|----------|---------------|----------------|
| **Padding** | 24px | 16px | Variable | 24px |
| **Border** | 1px gray | 1px subtle | 0-2px | 1px #2A2A2A |
| **Radius** | 8px | 4px | 0-16px | **0px** |
| **Shadow** | sm | None or custom | Layered | md shadow |
| **Hover** | Lift + shadow | Border color | Transform | Lift 4px + glow |

---

### 8. DATA TABLES

| Feature | StandardGT | Cirridae | HLTV/VLR | Recommendation |
|---------|------------|----------|----------|----------------|
| **Row Height** | 48px | 40px | 40-56px | **56px** |
| **Padding** | 16px | 12px | 8-16px | **16px horizontal** |
| **Border** | Bottom only | None | Bottom only | Bottom only |
| **Hover** | Background | None | Background | Background #262626 |
| **Sortable** | Yes | Yes | Yes | Yes |
| **Monospace** | Optional | No | Yes | **Yes for data** |

---

### 9. NAVIGATION

| Element | StandardGT | Cirridae | Awwwards SOTD | Recommendation |
|---------|------------|----------|---------------|----------------|
| **Header Height** | 64px | 56px | 60-80px | **64px** |
| **Sticky** | Yes | Optional | Common | Yes |
| **Mobile Menu** | Hamburger | Hamburger | Custom | Hamburger |
| **Breadcrumbs** | Text | Text | Minimal | **Text with separator** |
| **Active State** | Background | Underline | Various | **Underline + color** |

---

### 10. ANIMATIONS

| Type | StandardGT | Cirridae | Awwwards SOTD | Recommendation |
|------|------------|----------|---------------|----------------|
| **Duration** | 150-300ms | 200ms | 300-500ms | **200ms** |
| **Easing** | ease-out | ease | Custom cubic | **ease-out** |
| **Hover** | Scale + shadow | Color change | Transform | **Translate Y -4px** |
| **Page Load** | None | Fade in | Staggered | **Skeleton → content** |
| **Micro-interactions** | Minimal | Subtle | Extensive | **Subtle only** |

---

## SYNTHESIS: OUR DESIGN SYSTEM

Based on analysis of top frameworks and award-winning sites:

### Mandate These:
1. **0px border-radius** (sharp corners = premium)
2. **8px spacing scale** (consistent rhythm)
3. **56px table rows** (HLTV density)
4. **Monospace for data** (alignment)
5. **Vignette masks** (depth without shadows)
6. **200ms animations** (snappy feel)
7. **Mobile-first** (performance)

### Reject These:
1. **Rounded corners** (>4px = cheap/bootstrap)
2. **Feature bloat** (4 items max per view)
3. **Scroll on landing** (zero-scroll principle)
4. **Color overload** (5 colors max)
5. **Generic gradients** (solid colors only)

---

## REFERENCES

| Source | URL |
|--------|-----|
| StandardGT | https://github.com/StanJarvis/StandardGT |
| Cirridae CSS | https://cirrus-ui.com/ |
| VLR.gg | https://www.vlr.gg/ |
| HLTV.org | https://www.hltv.org/ |
| Awwwards | https://www.awwwards.com/ |

---

Table Version: 1.0.0
Last Updated: 2026-03-31
