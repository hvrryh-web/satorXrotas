[Ver001.000]

# OKRs — NJZ RAT-OS

**Status:** Active
**Cadence:** Quarterly
**Source:** Derived from PRD §4 KPIs and Phase milestones.

OKRs are aggressive but plausible. Hit 70% and you're winning.

---

## Annual Objective — Year 1

**O1. Validate the integration thesis at scale.**

Prove that a unified wellness-productivity OS retains and converts users meaningfully better than the fragmented status quo.

Year-1 key results (rolled up from quarterly):

- KR1: 250,000 MAU by Month 12.
- KR2: D30 retention ≥ 15% by Month 12.
- KR3: 5% free → paid conversion sustained for two consecutive months.
- KR4: NPS ≥ +45 in Month 12 cohort survey.
- KR5: Operationally profitable on recurring revenue by Month 12.

---

## Quarter 1 (Months 1–3) — *Ship the spine*

**O1.1. Land Phase 0 + Phase 1 MVP on the web.**

- KR1: All 8 Phase-0 workstreams merged on `main`; `pnpm build` green; `pnpm typecheck` zero errors.
- KR2: Phase 1 modules (Focus Hero, Soundscapes, Blocker, PolyCo Office shell) live in `apps/web` end-to-end.
- KR3: 5,000 MAU by end of Month 2; 12,000 MAU by end of Q1.
- KR4: D7 retention ≥ 18% in the Month-2 cohort.
- KR5: ≥ 10 active open-source contributors with at least one merged PR each.

**O1.2. Establish the engineering rhythm.**

- KR1: Average PR cycle time ≤ 36 hours.
- KR2: All architecture decisions captured in ADRs (zero "tribal" decisions in retros).
- KR3: 80% test coverage on `@njz-os/*` packages; 60% on `apps/*`.
- KR4: Pre-commit hook bypass count = 0.

---

## Quarter 2 (Months 4–6) — *Expand the surface*

**O2.1. Ship Phase 2 (Brain Training, Writing, Micro-Learning, PolyCo Home, mobile PWA).**

- KR1: All four Phase-2 modules launched; gates `G2.*` all OPEN.
- KR2: 25,000 MAU end of Month 4; 60,000 MAU end of Q2.
- KR3: D30 retention ≥ 10% in Month-4 cohort.
- KR4: Mobile PWA installable on iOS and Android, scoring ≥ 90 on Lighthouse PWA audit.

**O2.2. Open premium revenue.**

- KR1: Premium tier live with billing adapter integrated.
- KR2: 3% free → paid conversion in Month-4 cohort; 5% by end of Q2.
- KR3: 50% of D30-retained users sample at least one premium feature.

**O2.3. Social shell live (Phase 3 prep).**

- KR1: Friend invite flow shipped in PolyCo.World shell.
- KR2: Collaborative focus session design merged (ADR + prototype-system spec).

---

## Quarter 3 (Months 7–9) — *Network effects*

**O3.1. Phase 3 social features + native shells.**

- KR1: Native iOS + Android wrappers shipping (Capacitor or React Native — choice in ADR).
- KR2: Friend visits + collaborative focus sessions live.
- KR3: 150,000 MAU end of Q3.
- KR4: Seasonal event #1 shipped; 30% of DAU participates.

**O3.2. Operational profitability.**

- KR1: Recurring revenue covers hosting + content licensing costs.
- KR2: 6% free → paid sustained.
- KR3: Churn ≤ 8% monthly on premium tier.

---

## Quarter 4 (Months 10–12) — *Position for scale*

**O4.1. Reach Year-1 MAU target.**

- KR1: 250,000 MAU.
- KR2: D30 ≥ 15%.
- KR3: NPS ≥ +45.
- KR4: 1+ enterprise / B2B wellness pilot signed.

**O4.2. AI personalization layer.**

- KR1: Adaptive difficulty engine live across all training modules.
- KR2: Personalized soundscape recommendations (vaultbrain-driven).
- KR3: ≥ 25% lift in D7 retention vs non-personalized control.

---

## How These OKRs Are Measured

| KR type | Source of truth |
|---------|-----------------|
| MAU / DAU / Retention | `contracts/events/progression-events.json` events → analytics pipeline |
| Conversion | Billing adapter logs joined with cohort dimension |
| Engagement | Session events from focus / audio / blocker / writing / etc. |
| NPS | In-product survey, quarterly, cohorts ≥ 30 days |
| Engineering KRs | GitHub API + CI metrics + coverage reports |

Instrumentation lives in `packages/@njz-os/analytics`. Measurement definitions are versioned alongside this file.

---

## Updating OKRs

- Quarterly review on the last Friday of the quarter.
- Score each KR 0.0–1.0. Average is the objective score.
- Misses ≥ 0.4 below target: write a retro in `docs/dev-reports/DR-XXXX-q<n>-retro.md`.
- Drift requires an ADR (rare; OKRs should be stable within a quarter).
