[Ver001.000]

# ADR-0007 — `@njz/ui` Consumption Deferred Until Upstream Publishes

- **Status:** Accepted
- **Date:** 2026-05-24
- **Deciders:** @hvrryh-web
- **Tags:** integration, packages, ui, upstream-coordination, supersession

## Context

ADR-0002 ("Consume `@njz/*` Packages From Upstream") committed RAT-OS to consuming the entire `@njz/*` scope via npm, including `@njz/ui` for shared design primitives. Reality check against `notbleaux/ZeSporteXte` post-bootstrap:

- `packages/@njz/ui/` exists in the upstream repo, but it contains **only `src/components/`** — no `package.json`, no `tsconfig.json`, no `index.ts`, no build output, no version, no publish workflow. It is not a real npm package yet.
- `packages/adapters/api-client/src/generated/`-style or other `@njz/*` packages aren't published either, but those have less impact: they're behind adapters we control.
- RAT-OS's `@njz-os/ui` already ships local design tokens (colors, space, typography) that work for Phase 1's needs.

We cannot consume something that doesn't exist as a package, and we should not block Phase 1 work waiting for upstream to publish.

## Decision

**Defer `@njz/ui` consumption until upstream publishes a real package.** Specifically:

1. `@njz-os/ui` remains self-contained in RAT-OS for Phase 1. It carries its own tokens, primitives, and Tailwind preset.
2. RAT-OS does **not** declare `@njz/ui` as a dependency of any package in this repo until upstream ships:
   - A real `package.json` with a `name`, `version`, and `main`/`types` entries.
   - A semver-tagged release on GitHub Packages (or another registry RAT-OS can install from).
   - At least one published primitive (Button/Panel/Toggle) to validate the consumption pattern.
3. File an upstream issue at `notbleaux/ZeSporteXte` requesting the package be finalised. Link the issue from `.agents/active/upstream-coordination.md` here.
4. When upstream publishes, a follow-up ADR (likely ADR-0015 or later) records the migration plan: which `@njz-os/ui` primitives get replaced by `@njz/ui`, which tokens get re-anchored to the shared scope, and the deprecation window.

This decision **partially supersedes ADR-0002**: non-UI `@njz/*` packages remain in-scope for npm consumption when they ship (`@njz/vaultbrain-events`, `@njz/agent-protocol`, `@njz/auth-types`). Only the UI sub-decision is deferred.

## Consequences

**Positive:**

- Phase 1 implementation is not blocked on upstream package publication.
- `@njz-os/ui` evolves freely against RAT-OS-specific design needs (cozy pixel-art surfaces, productivity-app surfaces) without needing upstream coordination per change.
- One less moving piece during the most fragile pre-launch period.
- The upstream-coordination thread for ADR-0008 (vaultbrain) can carry the `@njz/ui` request as well — single coordination overhead instead of two.

**Negative:**

- Tech debt accrues. When `@njz/ui` does ship upstream, RAT-OS will need a one-time alignment pass: matching tokens, adopting primitives, deprecating any RAT-OS-only versions of components that exist upstream. Estimate: 1–2 sprints in Phase 2 or 3.
- The two design systems (`@njz-os/ui` here, `@njz/ui` upstream) may diverge in subtle ways during the deferral period, making the eventual migration noisier.

**Neutral:**

- Other `@njz/*` packages (vaultbrain-events, agent-protocol, auth-types) are unaffected by this decision. They remain on the ADR-0002 model: consume via npm when they ship.
- The brand surface (`NJZ RAT-OS` marketing copy; technical `njz-os`/`@njz-os/*` code) is unchanged.

## Alternatives Considered

- **Vendor a snapshot of upstream `packages/@njz/ui/src/`.** Rejected: nothing is there to vendor; even if there were, snapshots go stale fast and create import-path confusion.
- **Block Phase 1 on upstream publication.** Rejected: indefinite wait; PRD's Month-2 MVP target depends on Phase 1 shipping.
- **Publish `@njz/ui` ourselves from RAT-OS.** Rejected: violates the upstream/downstream contract; the platform owns NJZ-wide packages, not RAT-OS.
- **Rename `@njz-os/ui` to `@njz/ui` locally and resolve the collision later.** Rejected: namespace squatting against upstream invites painful conflicts; the `@njz-os/*` scope exists precisely to avoid this.

## Related

- ADR-0002 — Partially superseded by this ADR (UI sub-decision deferred; non-UI consumption retained).
- ADR-0012 (planned, Asset Pipeline) — will reference `@njz-os/ui` tokens; deferring `@njz/ui` keeps that ADR's surface stable.
- `packages/@njz-os/ui/README.md` — Phase-1 self-contained UI package.
- `.agents/active/upstream-coordination.md` — the coordination thread tracking the upstream `@njz/ui` publish request.
- Future migration ADR (TBD ADR-0015 or later) — alignment plan when upstream publishes.

---

> When proposing, leave Status: Proposed. On approval, change to Accepted in a follow-up commit.
> Append a one-line entry to `.agents/DECISION_LOG.md` referencing this ADR.
