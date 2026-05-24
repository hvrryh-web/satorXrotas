[Ver001.000]

# 04_REFERENCES

External authorities we defer to. Cite these instead of relitigating their conclusions in our own docs.

## Engineering

- [TC39](https://tc39.es/) — JavaScript / TypeScript language semantics.
- [Web.dev](https://web.dev/) — performance, accessibility, PWA patterns.
- [MDN Web Docs](https://developer.mozilla.org/) — Web API canonical reference.
- [TanStack Query docs](https://tanstack.com/query) — server state.
- [Zustand docs](https://zustand-demo.pmnd.rs/) — client state.
- [XState v5 docs](https://stately.ai/docs) — state machines.
- [Next.js docs](https://nextjs.org/docs) — App Router, SSG/ISR.
- [Vite docs](https://vitejs.dev/) — bundler.
- [Turborepo docs](https://turbo.build/repo/docs) — monorepo orchestration.
- [pnpm docs](https://pnpm.io/) — package manager.

## Design

- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) — accessibility.
- [Inclusive Components](https://inclusive-components.design/) — accessible UI patterns.
- [Refactoring UI](https://www.refactoringui.com/) — design heuristics.

## Audio

- [Web Audio API spec](https://www.w3.org/TR/webaudio/) — canonical.
- [Audio Worklet primer](https://developer.chrome.com/blog/audio-worklet) — low-latency audio processing.

## Domain — Cognitive Science

- [Lumosity neuropsychological reference set](https://www.lumosity.com/en/scientific-references/) — brain-training task validation.
- [CogniFit clinical assessment library](https://www.cognifit.com/science) — Corsi blocks, digit span standards.
- Doidge, N. *The Brain That Changes Itself* (2007) — neuroplasticity primer.
- Karpicke, J. D. (2012) — retrieval practice and learning retention.

## Domain — Productivity

- Newport, C. *Deep Work* (2016) — focused-work theory.
- Pink, D. *Drive* (2009) — intrinsic motivation and gamification.

## Citations Inside Docs

When a number appears in `docs/product/PRD.md` or `docs/product/MARKET_REVIEW.md`, it carries a footnote `[^N^]`. The footnote sources live with each doc, not here. This `04_REFERENCES/` directory is for *repo-wide authorities* — things you'd cite from many places.

## Adding a Reference

1. Confirm the source is durable (not a personal blog likely to vanish).
2. Add the entry under the right subsection.
3. If the reference replaces a prior authority, mark the prior as deprecated and note the supersession.
