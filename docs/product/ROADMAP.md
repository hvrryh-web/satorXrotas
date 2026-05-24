[Ver001.000]

# Roadmap — NJZ RAT-OS

**Status:** Active
**Source:** Synthesized from PRD §4.3 + uploaded `3NJZOS_Build_Plan.docx` (Month-by-month plan).

High-level milestones live in the root `ROADMAP.md`. This doc is the week-by-week tactical plan agents use to sequence work.

---

## Phase 0 — Foundation (Now → Week 2)

### Week 1 — Bootstrap

- Day 1: Repo wipe + new structure + legacy preservation branch (done in this commit).
- Day 1: Framework docs (`.agents/*`, `ROOT_AXIOMS/*`, `.doc-tiers.json`).
- Day 2: Product docs (PRD, OKRs, market review, personas, pricing).
- Day 3: Architecture docs + ADR-0001..0006.
- Day 4: Prototype-system specs PS-001..007.
- Day 5: Dev report DR-0001-bootstrap.

### Week 2 — Compile

- Day 6: Monorepo skeleton (`apps/site`, `apps/web`) compiles.
- Day 7: Package skeletons (`packages/@njz-os/*`) compile, type-check.
- Day 8: Adapter skeletons + OpenAPI surface stub.
- Day 9: CI pipeline green (lint + typecheck + tests).
- Day 10: Phase-0 retro + Phase-1 gate opening (ADR-0007..0010).

**Exit:** All `.agents/PHASE_GATES.md` Phase-0 gates `OPEN`. Phase-1 ADRs `Accepted`.

---

## Phase 1 — Core MVP (Month 1–2)

Headline: Focus Hero + Soundscapes + Distraction Blocker + PolyCo.World Office shell live in `apps/web` for the Balanced Achiever persona.

### Month 1 — Engines first

- Week 3: `@njz-os/focus-engine` (XState pomodoro + deep work) + adapter integration with vaultbrain.
- Week 4: `@njz-os/audio-engine` (5 minimum soundscapes + binaural beat oscillator pair).
- Week 5: `@njz-os/polyworld` (Canvas 2D isometric tile renderer + Office scene).
- Week 6: Distraction Blocker (web — block-list UI + service-worker enforcement on supported browsers; native deferred to Phase 3).

### Month 2 — Stitch + ship

- Week 7: `apps/web` route shells for 7 modules (only Focus, Sound, Blocker, PolyCo Office wired).
- Week 8: Onboarding flow + auth integration (passkeys + email).
- Week 9: Marketing site (`apps/site`) with hero + module previews + pricing page.
- Week 10: Public launch. Target: 5,000 MAU end of Month 2.

**Exit:** `G1.*` all OPEN. D7 retention ≥ 18% in cohort.

---

## Phase 2 — Expansion (Month 3–4)

Headline: Brain Training, Writing Space, Micro-Learning, PolyCo Home, mobile PWA. Premium tier live.

### Month 3 — Modules

- Week 11: Brain Training games 1–2 (Stroop, Corsi Blocks).
- Week 12: Brain Training games 3–5 (Digit Span, Memory Matrix, Match Pairs) + adaptive engine.
- Week 13: Writing Space editor + manuscript model + free exports.
- Week 14: Micro-Learning card renderer + first 50 cards + bookmark queue.

### Month 4 — World + revenue

- Week 15: PolyCo.World Home module + decoration system.
- Week 16: Mobile PWA (installable; Lighthouse PWA score ≥ 90).
- Week 17: Premium tier launch (billing adapter live).
- Week 18: Phase-2 retro. Target: 25,000 MAU.

**Exit:** `G2.*` all OPEN. D30 ≥ 10%. 3% free → paid in Month-4 cohort.

---

## Phase 3 — Social & Scale (Month 5–6)

Headline: Friend visits + seasonal events + native iOS / Android wrappers.

### Month 5 — Social

- Week 19: Friend system + invite flow.
- Week 20: Visit a friend's PolyCo.World + leave a token.
- Week 21: Collaborative focus sessions (shared timer, shared streak).
- Week 22: Seasonal event #1 (Summer Solstice).

### Month 6 — Native + scale

- Week 23: iOS native wrapper (Capacitor or React Native — ADR-0012).
- Week 24: Android native wrapper.
- Week 25: Native distraction-blocker integration (screen-time API).
- Week 26: Phase-3 retro. Target: 75,000 MAU.

**Exit:** `G3.*` all OPEN. Break-even on hosting.

---

## Phase 4 — Growth (Month 7–12)

- AI personalization layer (adaptive difficulty, content recommendations).
- Influencer + content partnership program.
- Enterprise / B2B wellness tier (first 5 pilot clients).
- Micro-Learning expansion to 500+ visual card sets.
- Strategic partnerships (wearable, calendar).
- Profitability on recurring subscription revenue.

Detailed weekly plan deferred until end of Phase 3 retro.

---

## Phase 5 — Platform (Month 13–24)

- 1M+ registered users.
- Creator economy (user-created PolyCo.World items, learning paths).
- i18n: 3+ languages.
- B2B wellness program scale (5+ corporate clients).
- Series A optionality evaluation.

---

## Risk-Adjusted Buffer

Every phase carries a one-week buffer not shown above. Use it for incident response, security patches, or scope creep recovery — not for new features.

## Updating This Doc

- Weekly: agents update the "current week" line item with status (done / on track / slipping).
- Per-phase retro: append a section to `docs/dev-reports/DR-XXXX-phase-<n>-retro.md`.
- Phase transition: open new phase logbook in `.agents/phase-logbooks/`.
