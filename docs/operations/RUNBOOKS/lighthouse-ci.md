[Ver001.000]

# Runbook — Lighthouse CI score regression

> **Owner:** Platform + Designer · **Trigger:** `Lighthouse CI` workflow report shows a category score below target.
> **Tool:** `@lhci/cli` + `lighthouserc.json` + `.github/workflows/lighthouse-ci.yml`.
> **Source item:** PRX-25-PERF-02.

---

## Targets (Phase-1)

| Category | Target | Mode |
|----------|--------|------|
| Performance | ≥ 0.85 | warn |
| Accessibility | ≥ 0.85 | warn |
| Best Practices | ≥ 0.90 | warn |
| SEO | ≥ 0.90 | warn |

PWA is intentionally not asserted in Phase 1 (manifest + SW arrive in Phase 2 per the EXPANDED.md).

`warn` mode allows merging on regression but surfaces the dip clearly. Tighten to `error` once 3 consecutive green main-branch runs establish the baseline.

---

## Triage when a category dips

### Performance

1. Open the LHCI report artifact for the failing run; navigate to the
   first failing URL.
2. Identify the top 3 diagnostic items by impact (largest contentful
   paint, total blocking time, cumulative layout shift).
3. Cross-reference with the **bundle-budget** workflow run on the same
   PR — perf regressions often correlate with bundle bloat.
4. Common fixes:
   - Image too large → `<picture srcSet=…>` + AVIF/WebP.
   - Render-blocking JS → split via `React.lazy`.
   - Web font flash → `font-display: swap` and preload critical weights.
   - 3rd-party script blocking main thread → defer / lazy-load.

### Accessibility

1. Filter the report by failing audit IDs.
2. Common Phase-1 fixes:
   - Missing landmarks → wrap each module route in `<main>` (Shell layout already does this).
   - Color contrast → verify against `tokens.json` meta.wcag annotations.
   - Image alt → add per `ROOT_AXIOMS/02_STANDARDS/01-doc-and-naming.md` content guidance.
   - Form labels → `<label htmlFor=…>` paired with `id`.

### Best Practices

1. CSP issues → review `apps/web/index.html` `<meta http-equiv="Content-Security-Policy">`.
2. Console errors → add an ErrorBoundary fallback (`@njz-os/ui`).

### SEO

1. Marketing-site SEO is owned by Lane E + uplift PRX-25-ENH-03 (streaming SSR).
2. Webapp routes intentionally `noindex` once Phase 1 auth wires up — score below SEO target on a webapp route is expected and the audit should be allowlisted via `skipAudits` rather than enforced.

---

## When to refresh the targets

- After every successful Phase-1 lane PR-merge, eyeball the artifact to
  confirm no dip; if perf jumped, optionally raise the target.
- When `error` mode flips (3 green runs), update this runbook to reflect
  the harder gate.
- When new routes ship (Phase 2: `/write`, `/learn`, `/train` get real
  content), add them to `lighthouserc.json` `ci.collect.url`.

---

## Cross-references

- `lighthouserc.json`
- `.github/workflows/lighthouse-ci.yml`
- `docs/program-management/PR-25-portfolio-uplift.md` §PRX-25-PERF-02
- `docs/operations/RUNBOOKS/bundle-budget.md` (related)
- `packages/@njz-os/ui/tokens/tokens.json` — palette + contrast annotations
