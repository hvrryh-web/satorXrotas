# eSports-EXE Design System

## Overview

The eSports-EXE Design System ensures visual consistency across all HUBs while enabling rapid development.

## Core Principles

1. **Dark Mode First**: Esports platforms are used for long sessions; dark mode reduces eye strain
2. **Progressive Disclosure**: Interfaces adapt to user expertise
3. **Data Density**: Information-rich displays for expert users
4. **Performance**: 60fps animations, <100ms interaction feedback

## Token System

Tokens are the atomic values of our design system. They are defined in:
- Tailwind config: `apps/web/tailwind.config.js`
- CSS variables: `apps/web/src/styles/tokens.css`

### Color Tokens

#### Background Colors
| Token | Value | Usage |
|-------|-------|-------|
| `--color-bg-primary` | `#0F172A` | Main background |
| `--color-bg-secondary` | `#1E293B` | Cards, panels |
| `--color-bg-tertiary` | `#334155` | Borders, dividers |

#### HUB Accent Colors
| HUB | Token | Value | Usage |
|-----|-------|-------|-------|
| ROTAS | `--color-accent-rotas` | `#14B8A6` | Stats, data tables |
| SATOR | `--color-accent-sator` | `#8B5CF6` | Analytics, charts |
| OPERA | `--color-accent-opera` | `#F97316` | Matches, live events |
| AREPO | `--color-accent-arepo` | `#EC4899` | Community, social |

#### Semantic Colors
| Token | Value | Usage |
|-------|-------|-------|
| `--color-success` | `#22C55E` | Positive states |
| `--color-warning` | `#EAB308` | Caution states |
| `--color-error` | `#EF4444` | Error states |
| `--color-info` | `#3B82F6` | Informational |

### Typography

#### Font Families
- **Headings**: Inter, system-ui, sans-serif
- **Body**: Inter, system-ui, sans-serif
- **Data/Monospace**: JetBrains Mono, monospace

#### Type Scale
| Token | Size | Usage |
|-------|------|-------|
| `text-xs` | 12px | Captions, timestamps |
| `text-sm` | 14px | Secondary text |
| `text-base` | 16px | Body text (minimum) |
| `text-lg` | 18px | Lead paragraphs |
| `text-xl` | 20px | Subheadings |
| `text-2xl` | 24px | Section headings |
| `text-3xl` | 30px | Page headings |
| `text-4xl` | 36px | Hero headings |

### Spacing Scale

Base unit: **4px**

| Token | Size | Usage |
|-------|------|-------|
| `space-1` | 4px | Tight spacing |
| `space-2` | 8px | Default element gap |
| `space-4` | 16px | Component padding |
| `space-6` | 24px | Section padding |
| `space-8` | 32px | Large gaps |
| `space-12` | 48px | Page sections |
| `space-16` | 64px | Major divisions |

## Components

### Button

**Variants:**
- `primary` — Main actions
- `secondary` — Alternative actions
- `ghost` — Low emphasis
- `danger` — Destructive

**Sizes:**
- `sm` — Compact
- `md` — Default
- `lg` — Prominent

**Usage:**
```tsx
<Button variant="primary" size="md">
  View Stats
</Button>
```

### Card

**Variants:**
- `default` — Content container
- `interactive` — Clickable with hover
- `stat` — Data display
- `match` — Match summary

**Usage:**
```tsx
<Card variant="stat" accent="rotas">
  <StatLabel>KDA</StatLabel>
  <StatValue>1.45</StatValue>
</Card>
```

### Input

**Variants:**
- `text` — Standard input
- `search` — With search icon
- `select` — Dropdown
- `toggle` — Boolean switch

## Layout Patterns

### HUB Layout
All HUBs follow a consistent structure:
```
[Navigation]
[Hero/Header]
[Content Grid]
  [Main Panel] [Side Panel]
[Footer]
```

### Progressive Disclosure

**Casual View:**
- Scores and schedules only
- Large touch targets
- Minimal text

**Aspiring View:**
- Match details
- Player stats
- Basic charts

**Professional View:**
- Raw data tables
- Customizable dashboards
- Advanced filtering

## Accessibility

### Requirements
- WCAG 2.1 AA compliance minimum
- Color contrast 4.5:1 for text
- Keyboard navigation support
- Screen reader compatibility

### Implementation
- Semantic HTML elements
- ARIA labels where needed
- Focus indicators visible
- Reduced motion support

## Implementation

### Tailwind Configuration

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        background: {
          primary: '#0F172A',
          secondary: '#1E293B',
          tertiary: '#334155',
        },
        accent: {
          rotas: '#14B8A6',
          sator: '#8B5CF6',
          opera: '#F97316',
          arepo: '#EC4899',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
}
```

### Component Library

Components are built in `apps/web/src/components/ui/`

Each component must have:
- TypeScript types
- Storybook story
- Usage documentation
- Accessibility tests

## Resources

- [Master Plan](../master-plan/master-plan.md#4-design-system-contracts)
- [ADR-003: Design Tokens](../adrs/adr-003-design-tokens.md)
- Figma Design File: [Link TBD]

---

*For questions or proposals, create an ADR or consult the Master Plan.*
