# Writing editor bench — PRX-25-SPRINT-01

> **Purpose:** settle ADR-0015 (editor library — Tiptap recommended in
> Writing Space EXPANDED.md §11) with empirical evidence on the chapter
> sizes our P95 user will produce (≤ 80 KB markdown).
> **Status:** scaffold landed; full bench results pending session
> capacity.

## Hypothesis

Tiptap (default recommendation) outperforms ProseMirror-raw and Lexical
on mobile-keyboard latency and bundle size at the chapter sizes our
P95 user produces.

## Ship rule

If Tiptap wins ≥ 2 of:

- time-to-first-keystroke
- p95 keystroke-to-paint
- bundle-size
- iOS-Safari quirks count

then ADR-0015 records "Tiptap". Else escalate to user via
`AskUserQuestion` with the data summary.

## Methodology

1. Three sandbox routes mounted under `apps/web/src/dev/editor-bench/{tiptap,prosemirror,lexical}.tsx` (out-of-scope for this scaffold — wires up when one of those editor libs ships).
2. Each route loads the same 80 KB markdown fixture from `bench/fixtures/`.
3. Measurement harness:
   - **TTI** via `performance.timing.responseEnd → DOMContentLoaded`.
   - **Keystroke-to-paint p50 / p95 / p99** — `dispatchEvent(KeyboardEvent)` 1000 times scripted, `performance.measure` each round-trip.
   - **Bundle size** — Vite `rollup-plugin-visualizer` JSON output diffed per route.
   - **iOS-Safari quirks** — manual checklist run on iPhone 12 Safari.
4. Run on:
   - Desktop Chrome (baseline)
   - iPhone 12 Safari (mobile)
   - Pixel 6 Chrome (mid-range Android)

## Output

- `docs/dev-reports/DR-W-editor-bench.md` — raw numbers + recommended ADR-0015 verdict.
- Raw CSVs in `bench/output/` (gitignored except the summary).

## Wiring

This scaffold doesn't include the actual harness — the harness lives in
`apps/web/src/dev/editor-bench/` and is guarded behind `NJZ_DEV_BENCH`
so production builds never ship it. Land the harness in the same PR
as the first editor library install.
