[Ver001.000]

# RISK_REGISTER — NJZ RAT-OS

> **Purpose:** every "out of scope", "queued for follow-up", "deferred",
> or "blocked" item across the project lives here as one row, scored
> Likelihood × Impact, with a refresh trigger (what unblocks it).
> Replaces ad-hoc out-of-scope bullets scattered through PR bodies.
> **Status:** active. Refreshed per session arc + on every PR that
> resolves or adds a risk row.
> **Authored:** 2026-05-30 (post Phase-1 lane sweep).

---

## Scoring

| Dimension | 1 | 2 | 3 |
|-----------|---|---|---|
| **Likelihood** | unlikely (< 25 %) | possible (25-75 %) | likely (> 75 %) |
| **Impact** | low (cosmetic / single-lane delay) | medium (blocks one gate / lane) | high (blocks Phase exit / multi-lane) |

Risk score = L × I (1..9). Triage:
- **1-2** monitor; refresh per session
- **3-4** open a follow-up issue; assign owner
- **6-9** escalate to user; consider rebudgeting

---

## Active rows (2026-05-30 snapshot)

| ID | Origin | Risk | L | I | Score | Trigger / mitigation | Owner |
|----|--------|------|---|---|-------|----------------------|-------|
| R-001 | Lane A | A3 vaultbrain wiring deferred; ProgressionEvents emit nowhere yet | 3 | 2 | 6 | Trigger: EPIC-01 already shipped; just wire onStart/onComplete/onAbandon to client. Owner: Implementer (next session). | unowned |
| R-002 | Lane A | A7 Playwright E2E deferred | 2 | 2 | 4 | Trigger: A3 ships; then E2E is a thin shell over the reducer. | unowned |
| R-003 | Lane B | B5 Deep Canvas painter deferred | 2 | 2 | 4 | Trigger: AnalyserNode tap is live in graph.ts; painter is straightforward rAF loop. | unowned |
| R-004 | Lane B | B6 iOS resume + visibility-change quirks unhandled | 2 | 3 | 6 | Trigger: requires manual iOS device testing; combine with B5 PR. | unowned |
| R-005 | Lane B | Audio plays no actual sound (SoundActive is UI-only) | 3 | 1 | 3 | Trigger: AudioContext wire-up combined with B5. | unowned |
| R-006 | Lane C | C1 Aseprite + FFmpeg pipeline not landed | 2 | 3 | 6 | Trigger: tool install + script authoring. Until then WorldRoute renders schematic CSS grid. | unowned |
| R-007 | Lane C | C2 shared palette + seed asset set not landed | 2 | 2 | 4 | Trigger: design pass; combine with C1. | unowned |
| R-008 | Lane D | D2 service worker not registered | 2 | 3 | 6 | Trigger: Vite PWA plugin + fetch-intercept + interstitial route. | unowned |
| R-009 | Lane D | D4 Chrome MV3 extension not started | 2 | 2 | 4 | Trigger: new `apps/browser-extension/` workspace; Web Store review 1-3 weeks. | unowned |
| R-010 | Lane D | D5 Google Calendar + Apple CalDAV OAuth not wired | 2 | 2 | 4 | Trigger: Lane E E4 (Supabase) must ship first. | blocked-on R-013 |
| R-011 | Lane D | D7 E2E + Web Store submission + gate flip deferred | 2 | 2 | 4 | Trigger: D2 + D4 ship. | unowned |
| R-012 | Lane E | E4 real WebAuthn passkey UX + virtual-authenticator E2E deferred | 3 | 2 | 6 | Trigger: SUPABASE_URL + SUPABASE_ANON_KEY env vars. | needs user input |
| R-013 | Lane E | Supabase project credentials missing | 3 | 3 | 9 | **ESCALATE.** Trigger: user provisions Supabase + adds env vars. | user |
| R-014 | Lane E | E8 security review + detect-secrets baseline + CSP + WCAG 2.2 AA audit deferred | 2 | 3 | 6 | Trigger: final Lane E PR before Phase-1 exit. | unowned |
| R-015 | PRX-25 | PERF-03 B′ frame-budget instrumentation gated on B′ lane code | 2 | 2 | 4 | Trigger: B′ lane code starts. | blocked-on Phase-2 entry |
| R-016 | PRX-25 | ENH-04 cohort percentiles gated on B′ lane code + upstream cron | 2 | 2 | 4 | Trigger: same as R-015 + upstream cron design. | blocked-on Phase-2 entry |
| R-017 | PRX-25 | SPRINT-01 editor bench scaffold landed but full run deferred | 1 | 2 | 2 | Trigger: dedicated offline session running the harness against 80 KB fixture. | unowned |
| R-018 | PRX-25 | SPRINT-02 SRS bench scaffold landed but full cohort run deferred | 1 | 2 | 2 | Trigger: dedicated offline session running the cohort simulator. | unowned |
| R-019 | Infra | Per-page bundle attribution for Next.js SSR/SSG routes uses total-chunk-sum heuristic | 2 | 1 | 2 | Trigger: walk `.next/app-build-manifest.json` for per-route attribution. | unowned |
| R-020 | Infra | Lighthouse CI thresholds set to `warn`; tighten to `error` after 3 green main runs | 2 | 1 | 2 | Trigger: 3 consecutive green runs. | auto-triggered |
| R-021 | Phase 1 | `G1.*` gates still LOCKED despite source ADRs Accepted and lane slices shipped | 3 | 3 | 9 | **ESCALATE.** Trigger: PHASE_GATES.md needs refresh; coordinator follow-up. Note: lanes are not yet fully closed (A 5/8, B 5/8, C 5/7, D 3/7, E 6/8), so unlock criteria not yet met. Manifest review needed. | this session refreshes the table |
| R-022 | Phase 1 | DR-0002 (Phase-1 launch dev report) not authored | 2 | 2 | 4 | Trigger: all G1.* gates OPEN + Lighthouse audit. | unowned |
| R-023 | Upstream | Vaultbrain extension (ADR-0008 Option A) — upstream issue #118 still open | 3 | 3 | 9 | **ESCALATE.** Trigger: 2-week timer to 2026-06-07; on no signal, fall back to Option B (`services/rat-os-state` in this repo). | unowned |
| R-024 | Upstream | `@njz/ui` upstream package (ADR-0007) — upstream issue #117 still open | 2 | 2 | 4 | Trigger: upstream packaging effort; `@njz-os/ui` remains self-contained until then. | unowned |
| R-025 | Governance | DECISION_LOG narrative-only; no structured verification matrix | 2 | 2 | 4 | Trigger: verification matrix produced from `tools/verification-matrix/` (queued INFRA). | this session adds the protocol doc; tool follows |

---

## Closed rows (audit trail)

| ID | Closure date | Closure mechanism |
|----|--------------|-------------------|
| (none yet — register opens 2026-05-30) | | |

---

## Refresh trigger checklist

When any of these events fires, refresh this register in the same PR:

- A PR closes one of the rows above → move to "Closed rows".
- A PR introduces a new "out of scope" follow-up → add a row.
- A row's likelihood or impact materially changes → re-score.
- A row's trigger date elapses without resolution → escalate.

---

## Cross-references

- `docs/governance/LANE_CLOSURE_MANIFEST_TEMPLATE.md` — out-of-scope rows feed here.
- `.agents/handoff/*.md` — session-close handoffs reference active high-score rows.
- `.agents/active/upstream-coordination.md` — upstream-coordination follow-ups (R-023, R-024).
- `docs/program-management/PR-25-portfolio-uplift.md` §G.1 — uplift status (R-015..R-018).

---

*Living document. Update in the same PR that adds or closes a row.*
