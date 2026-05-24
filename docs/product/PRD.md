[Ver001.000]

# PRD — NJZ RAT-OS

**Status:** Accepted (Phase 0)
**Owner:** Product / @hvrryh-web
**Source:** Refined from uploaded `3NJZOS_PRD.docx` (July 2025) — NJZ RAT-OS brand alignment and ZeSporteXte integration added.

---

## 1. Executive Summary

### 1.1 Product Vision

NJZ RAT-OS — *Your Neural Operating System* — is a unified wellness-productivity platform that replaces app fragmentation with a single, cohesive cognitive environment. It integrates seven previously separate utilities (Focus Training, Soundscapes & Frequencies, Distraction Blocking, Writing Space, Micro-Learning, Gamified Productivity, and PolyCo.World metaverse) into one product where every action in any module feeds a unified progression system.

The thesis: productivity and wellness are complementary states of one neural system. A platform that integrates both — and renders progress as a shared metaverse — engages users in ways no standalone competitor can match.

### 1.2 PolyCo.World — The Connective Tissue

PolyCo.World is a cozy pixel-art isometric metaverse that transforms RAT-OS from a feature bundle into a living ecosystem. Two modules:

- **Office** — productivity headquarters (Focus Hero command desk, Writing Space cabin, Brain Training dojo, Micro-Learning library). Real-world productive actions manifest visibly here.
- **Home** — wellness sanctuary (Soundscapes garden, Distraction Blocker shield room, Sleep cave, Meditation zen space). Wellness usage beautifies and expands this space.

This dual-module architecture mirrors the core philosophy: productivity without wellness leads to burnout; wellness without productivity leads to stagnation.

### 1.3 Market Opportunity (Refined)

Combined addressable market exceeds **$25B** across brain training ($9.76–16.26B), focus management ($3.72B), sound therapy ($1.12B → $9.5B by 2032), distraction blocking ($1.4–2.37B → $7.02B by 2033), creative writing ($4.96B), and micro-learning ($3.01–5.06B).

Three structural inefficiencies RAT-OS exploits:

1. **Subscription fatigue.** Users paying $210–370/year across 5+ apps that don't talk to each other.
2. **Conversion premium in cognitive wellness.** Brain training averages 6–9% freemium-to-paid (vs 3–5% industry baseline).
3. **No competitor combines premium audio with visual storytelling.** RAT-OS's *Deep Canvas Hush* signature is whitespace.

### 1.4 Zero-Budget Execution

MVP infrastructure cost: $0. All core dependencies are open-source. Detail in `docs/operations/DEPLOYMENT.md` and the upstream Build Plan synthesis at `docs/product/ROADMAP.md`.

---

## 2. Product Overview

### 2.1 Identity

| Field | Value |
|-------|-------|
| Brand | **NJZ RAT-OS** |
| Tagline | "Train. Focus. Create. Learn. Grow." |
| Category | Wellness-productivity OS / gamified lifestyle platform |
| Primary surfaces | Responsive web, iOS / Android (PWA → native), Desktop widget |
| Monetization | Freemium (cosmetic items, advanced analytics, premium soundscapes behind subscription) |
| Phase 1 target | Web MVP at Month 2 |
| Phase 3 target | Full platform at Month 6 |

### 2.2 Three Surfaces, One Backend

- **Marketing site** (`apps/site`, Next.js 15, SSG/ISR) — public entry; cold visitors.
- **Webapp** (`apps/web`, Vite + React 19) — authenticated daily-use surface; all seven modules + PolyCo.World.
- **Desktop widget** (`apps/desktop-widget`, Tauri, Phase 2+) — always-on focus timer + soundscape + mini-world view.

All surfaces share state via vaultbrain (`packages/adapters/vaultbrain-client`). User can start a focus session on mobile, continue writing on desktop, check world progress on web — seamlessly.

### 2.3 Value Proposition

Quantifiable consolidation. Maintaining equivalent functionality through separate apps costs $285–345/year. RAT-OS Premium projects at $39.99/year — savings of **$245–305/year (86–88%)**.

Beyond cost: integration creates *emergent value*. Brain training scores raise Focus Hero XP rates. Writing streaks unlock learning content discounts. Soundscape usage during focus generates joint analytics correlating audio environments with productivity output. No single-purpose competitor can replicate this loop.

---

## 3. Target Users

Three distinct tiers. Detailed personas in `docs/product/PERSONAS.md`.

| Tier | Range | Engagement | Price tolerance | LTV |
|------|-------|------------|-----------------|-----|
| **Primary — Balanced Achiever** | 18–35, students + early-career | 20–45 min × 2/day | $30–50/yr | $45–75 (18mo) |
| **Secondary — Creative Professional** | 25–45, remote workers + writers + devs | 45–90 min × 1–2/day | $50–80/yr | $80–150 (24mo) |
| **Tertiary — Curious Learner** | 13–25, students + gamers | 15–30 min × 3–5/wk | Free-first | $5–15 (6mo) |

Combined addressable users: 170M+ globally (sum of Primary + Secondary + Tertiary indicators).

---

## 4. KPIs & Targets

### 4.1 Primary KPIs (Months 2 → 12)

| Metric | M2 | M4 | M6 | M12 |
|--------|----|----|----|-----|
| MAU | 5,000 | 25,000 | 75,000 | 250,000 |
| DAU | 1,000 | 5,000 | 15,000 | 50,000 |
| DAU/MAU | 20% | 20% | 20% | 20% |
| D1 retention | 35% | 40% | 45% | 50% |
| D7 retention | 18% | 22% | 25% | 30% |
| D30 retention | 8% | 10% | 12% | 15% |
| Avg session duration | 12 min | 15 min | 18 min | 20 min |
| Sessions / user / day | 1.5 | 1.8 | 2.0 | 2.2 |
| PolyCo.World DAU | 400 | 3,000 | 10,000 | 35,000 |
| Free → paid conversion | — | 3% | 5% | 7% |
| NPS | — | +25 | +35 | +45 |

### 4.2 Module Engagement Targets (Month 6)

| Module | % of DAU using | Avg session | 7-day streak share |
|--------|----------------|-------------|---------------------|
| Focus Hero | 65% | 25 min | 40% |
| Soundscapes | 55% | 35 min | 35% |
| Brain Training | 40% | 12 min | 30% |
| Distraction Blocker | 35% | 30 min | 25% |
| Writing Space | 20% | 40 min | 15% |
| Micro-Learning | 30% | 10 min | 28% |
| PolyCo.World | 45% | 15 min | 35% |

KPI instrumentation lives in `contracts/events/progression-events.json`. Measurement methodology in `docs/product/OKRS.md`.

### 4.3 Phase Milestones

| Phase | Window | Headline |
|-------|--------|----------|
| 0 — Foundation | Now → Week 2 | Framework + skeleton merged |
| 1 — Core MVP | Month 1–2 | Focus Hero + Soundscapes + Blocker + PolyCo Office shell → 5K MAU |
| 2 — Expansion | Month 3–4 | Brain Training + Writing + Micro-Learning + PolyCo Home + PWA → 25K MAU |
| 3 — Social & Scale | Month 5–6 | Friend visits + events + native apps → 75K MAU |
| 4 — Growth | Month 7–12 | Influencer + enterprise + AI personalization → 250K MAU |
| 5 — Platform | Month 13–24 | Creator economy + i18n + Series A optionality → 1M users |

---

## 5. Module Specifications

Each module has its own detailed spec in `docs/prototype-systems/`. Summary index:

| Module | Spec | Phase |
|--------|------|-------|
| Focus Hero (Gamified Focus) | `PS-001-focus-hero.md` | 1 |
| Soundscapes & Frequencies | `PS-002-soundscapes.md` | 1 |
| Distraction Blocker | `PS-003-distraction-blocker.md` | 1 |
| Writing Space | `PS-004-writing-space.md` | 2 |
| Micro-Learning | `PS-005-micro-learning.md` | 2 |
| Brain Training | `PS-006-brain-training.md` | 2 |
| PolyCo.World | `PS-007-polyco-world.md` | 1 (shell) → 2 (Home) → 3 (social) |

The PRD-level summaries below cover headline behaviour. Implementation detail lives in the PS files.

### 5.1 Focus Training (`PS-006`) + Focus Hero (`PS-001`)

Five brain training games at launch (Stroop, Corsi Blocks, Digit Span, Memory Matrix, Match Pairs). Each game maps to a cognitive domain with adaptive difficulty (±15% based on rolling 7-session performance).

A *My Journey* progression system: 10 chapters × 20–30 steps, three skill trees (Memory, Attention, Speed), unlock gates between chapters. Daily Workout: 3 games (strength + weakness + random), 10–15 min, generates Neural Dust for PolyCo.World.

Focus Hero overlays: pomodoro / deep-work timer with XP, streaks, hero progression. Every focus session unlocks decorations in the Office module.

### 5.2 Soundscapes & Frequencies (`PS-002`)

Four states (Focus, Relax, Sleep, Meditate), five environmental themes (Nature, Urban, Cosmic, Minimal, Instrumental), 40 tracks at launch (30-min seamless loops).

**Deep Canvas Hush** — signature audio-visual experience. Full-screen generative canvas reactive to audio FFT; "paints" itself over session duration; final artwork saved to user gallery and usable as PolyCo.World wall art. Differentiator vs all audio-only competitors.

Binaural beat presets (Delta / Theta / Alpha / Beta / Gamma) with *Find My Frequency* onboarding wizard. 3D brain visualization reflects frequency activity.

### 5.3 Distraction Blocker (`PS-003`)

Four enforcement levels (Gentle / Moderate / Strict / Maximum). Block categories: Social Media, Entertainment, Messaging, Shopping, News, Games. Calendar integration auto-blocks during "Focus" / "Deep Work" / "Study" events. Override cooldown: 60 seconds, max 3 overrides/day, configurable.

Focus Score (0–100) per session. PolyCo.World shield room visualises active blocks; streaks unlock Iron Will and Fortress decorations.

### 5.4 Writing Space (`PS-004`)

Distraction-free chapter editor, mobile-first. Space Grotesk + Inter typography. Light / dark / sepia themes. Project dashboard with word-count tracking, writing calendar heat map, character / setting trackers.

Exports: PDF + Markdown + plain text (free); EPUB + DOCX (premium). Voice-to-text dictation with brainstorm mode.

Every chapter completion adds a book to the PolyCo.World cabin bookshelf. 50K+ words unlocks Author's Quill legendary decoration.

### 5.5 Micro-Learning (`PS-005`)

Bite-sized visual card lessons inspired by Imprint's format. Tap-forward interaction. Content types: Quick Read (5–10 cards), Series (multi-day), Deep Dive (15–25 cards). Spaced-repetition queue for bookmarked cards (SM-2 algorithm).

Connection Cards link to related concepts. Card completion populates the PolyCo.World library.

### 5.6 PolyCo.World (`PS-007`)

Pixel-art isometric metaverse. Office + Home dual modules (see §1.2). Decoration system tied to module progress. Hero character with stats (Focus / Creativity / Wellness / Knowledge). Friend visits + collaborative focus sessions (Phase 3). Seasonal events and limited-time content (Phase 3). Creator economy (Phase 5).

---

## 6. Integration With ZeSporteXte

RAT-OS is a *sibling* product to the eSports platform in `notbleaux/ZeSporteXte`. Both share the NJZ family conventions, the `@njz/*` package scope, and a subset of platform services. RAT-OS does not duplicate ZeSporteXte; it consumes.

### 6.1 Shared Services (Consumed via Adapters)

| Upstream service | RAT-OS adapter | Purpose |
|------------------|----------------|---------|
| `services/vaultbrain` | `packages/adapters/vaultbrain-client` | Persistent state + AI memory; cross-device sync |
| `services/agent-gateway` | `packages/adapters/agent-gateway-client` | In-app AI helpers; MCP routing |
| `services/api` | `packages/adapters/api-client` | REST data plane; OpenAPI-generated |
| (TBD: `services/identity`) | `packages/adapters/identity-client` | Auth / session management |

Full contract surface in `contracts/openapi/njz-rat-os.yaml`. Integration architecture in `docs/architecture/INTEGRATION_WITH_ZESPORTEXTE.md`.

### 6.2 Shared Packages (npm scope `@njz/*`)

| Package | Use in RAT-OS |
|---------|---------------|
| `@njz/ui` | Re-exported and extended by `@njz-os/ui` for RAT-OS-specific primitives |
| `@njz/vaultbrain-events` (planned) | Wrapped by vaultbrain-client adapter |
| `@njz/agent-protocol` (planned) | Wrapped by agent-gateway-client adapter |

### 6.3 What RAT-OS Does *Not* Inherit

- TENET / GameNodeID / Quarter GRID — eSports-specific topology, out of scope.
- VCT / Valorant / CS2 data pipelines — eSports analytics, out of scope.
- Hub-1..5 frontend hubs — separate product surface.

---

## 7. Monetization

### 7.1 Freemium Structure

- **Free tier:** all 7 modules with core functionality; PolyCo.World with default decorations; basic analytics; ad-free.
- **Premium tier ($39.99/year promotional, then $59.99/year):**
  - Detailed cognitive analytics + historical trends + brain age estimate + CSV/JSON export
  - Premium soundscapes (Deep Canvas advanced themes, 8-hour Sleep Painting)
  - Distraction blocker advanced enforcement (uninstall protection, settings lock)
  - Writing Space premium exports (EPUB, DOCX, custom covers)
  - PolyCo.World cosmetic catalogue access + seasonal exclusives
  - Sync across 5+ devices
  - Priority support

### 7.2 Other Revenue Streams (Phase 3+)

- One-time cosmetic packs for PolyCo.World
- Themed bundles around seasonal events
- Team/enterprise tier for corporate wellness programs (Phase 4)
- Creator economy revenue share (Phase 5)

Pricing rationale in `docs/product/PRICING.md`.

---

## 8. Out of Scope (MVP)

- Medical claims (binaural beats labelled as "effects vary; not a medical treatment").
- Clinical diagnosis (analytics are educational, not diagnostic).
- Real-money trading in PolyCo.World.
- Loot boxes / gacha mechanics.
- Per-module standalone apps (against the integration thesis).

---

## 9. Open Questions

| Question | Owner | Decision-by |
|----------|-------|-------------|
| Auth model: passkeys-only vs passkeys + email? | Architect | Pre-Phase-1 |
| Mobile native: Capacitor vs React Native? | Architect | Pre-Phase-2 |
| Pricing: $39.99 launch promo duration? | Product | Pre-Phase-2 |
| Content licensing: original tracks vs CC-licensed? | Product + Legal | Pre-Phase-1 |
| EU GDPR readiness timeline | Security | Pre-Phase-3 |

---

## 10. References

Citations from the source PRD `[^N^]` are preserved in `docs/product/MARKET_REVIEW.md`. Source data on competitor pricing, market sizing, conversion benchmarks lives there.
