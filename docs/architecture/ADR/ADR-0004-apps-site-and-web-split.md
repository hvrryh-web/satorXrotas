[Ver001.000]

# ADR-0004 — `apps/site` (Next.js) and `apps/web` (Vite + React) Split

- **Status:** Accepted
- **Date:** 2026-05-24
- **Deciders:** @hvrryh-web
- **Tags:** apps, framework, marketing, webapp

## Context

RAT-OS has two distinct audiences and two distinct workloads:

- **Marketing surface.** Public, anonymous, SEO-critical, cold-start latency matters. Mostly static content with occasional CMS-driven updates.
- **Webapp surface.** Authenticated, heavy on audio + canvas + WebGL + WebSocket, returning users daily.

A single framework forced to do both compromises one or the other.

## Decision

Two apps in the monorepo:

- **`apps/site`** — Next.js 15 (App Router), SSG/ISR-first. Vercel-hosted with edge runtime. Optimised for first paint and SEO.
- **`apps/web`** — Vite + React 19 SPA. Vercel-hosted as static + SPA. Optimised for runtime interactivity, audio latency, WebSocket throughput.

Shared:

- Design tokens (via `@njz-os/ui`).
- Domain types (via `@njz-os/core`).
- Adapter clients (via `packages/adapters/*`).
- Identity / auth session cookie domain.

Distinct:

- Routing (Next App Router vs React Router / TanStack Router in the webapp).
- Rendering paradigm (RSC vs CSR).
- Build target.

## Consequences

**Positive:**

- Best tool for each job. Next is best-in-class for marketing/content; Vite SPA is best-in-class for rich client apps with audio/canvas.
- Smaller webapp bundle (no Next runtime overhead in `apps/web`).
- Marketing site can pre-render at build time; instant TTFB.
- Independent deployments: marketing copy ships without webapp redeploy.

**Negative:**

- Two build systems to learn. Mitigation: Turborepo orchestrates both; one `pnpm dev` command.
- Two route configurations. Mitigation: docs cover both clearly.
- Shared session cookie requires same-domain hosting. Mitigation: configure via Vercel domains.

**Neutral:**

- Designers see two surfaces. Mitigation: shared `@njz-os/ui` keeps look-and-feel unified.

## Alternatives Considered

- **Single Next.js app for both.** Rejected: heavy bundle for the audio/canvas workload; SPA pages awkward within Next App Router; SSR overhead unnecessary for authenticated webapp routes.
- **Single Vite SPA for both.** Rejected: SEO and first-paint for marketing pages poor without SSR; pre-rendering Vite SPA is doable but a worse experience than Next SSG.
- **Astro for the marketing site.** Rejected: smaller ecosystem, additional framework to maintain, Next handles our needs.
- **Remix.** Considered; Next chosen for ecosystem maturity (esp. Vercel deploy integrations) and broader agent familiarity.

## Related

- ADR-0001 (Monorepo structure)
- `docs/architecture/SYSTEM_OVERVIEW.md`
- `infra/vercel/site.json`, `infra/vercel/web.json`
