# Learning-cards SRS bench — PRX-25-SPRINT-02

> **Purpose:** settle SM-2 (default recommendation in Micro-Learning
> EXPANDED.md §4) vs FSRS-5 with offline simulation on a synthetic
> cohort, before ADR-0016 / 0017 sequencing commits.
> **Status:** scaffold + simulator stub landed; full bench run pending.

## Hypothesis

SM-2 + interval-jitter ± 10 % retains ≥ 92 % of FSRS-5's review
efficiency at < 30 % of FSRS-5's per-review compute and parameter
complexity for our Phase-2 cohort (N < 50 cards/user/week).

## Ship rule

If SM-2 retains ≥ 90 % efficiency at < 50 % complexity → ship SM-2 +
jitter (no new ADR; document choice in `docs/dev-reports/`).

Else → open ADR-0020 (FSRS-5 adoption) with the comparative data.

## Methodology

1. Synthetic cohort generator — `generateCohort()` produces 1 000
   users × 365 days × 50 cards/user with three forgetting-curve
   shapes:
   - **Steep** (fast forgetting, hard subject): half-life 24 h.
   - **Medium** (typical adult learner): half-life 5 days.
   - **Shallow** (familiar subject): half-life 21 days.
2. Both algorithms run side-by-side over the cohort with their default
   parameters.
3. Metrics collected per algorithm per user:
   - **Total reviews** to reach 90 % retention at 30 days.
   - **Mean retention** at 7 / 30 / 90 days.
   - **Time-to-mastery** (first 5 consecutive quality ≥ 4 reviews).
   - **Review-burden** p50 / p95 (cards due per day, rolling 7-day window).

## Output

- `docs/dev-reports/DR-L-srs-bench.md` — summary + verdict.
- Raw CSVs in `bench/output/` (gitignored except summary).

## Files in this scaffold

- `simulator.ts` — pure TS reference SM-2 + FSRS-5-lite implementation
  (stub; expand to full bench in follow-up).
- `cohort.ts` — synthetic cohort generator.
- `README.md` (this file).

## Why scaffold-now, run-later

Running the full simulation requires:

- The full FSRS-5 parameter set (offline review of the FSRS algorithm
  paper).
- A reproducible RNG seed for cohort generation.
- Output CSV writers and chart generators.

Scaffolding the harness now means an ADR-0016 review can run the bench
on its own time without scaffolding becoming the bottleneck.
