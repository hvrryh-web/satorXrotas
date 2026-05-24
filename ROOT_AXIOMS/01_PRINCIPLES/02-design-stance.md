[Ver001.000]

# PR-02 — Design Stance

## Aesthetic

- **Cozy + precise.** Pixel-art warmth in PolyCo.World; geometric minimalism in productivity surfaces.
- **Sharp corners (0–4px radius) on functional UI; rounded only inside the metaverse.** Sharp signals "tool"; rounded signals "play".
- **Two type families:** Space Grotesk for headlines + UI; Inter for body. No third family without an ADR.
- **Dark by default**, light theme available. Both must score AA contrast.

## Tokens, Not Hex

Every colour, spacing, and radius comes from `@njz-os/ui/src/tokens`. Hardcoded values are PR-blocking.

## Motion

- Purposeful, not decorative.
- Default duration: 150ms. Easing: `cubic-bezier(0.2, 0.8, 0.4, 1)`.
- Respect `prefers-reduced-motion`. Always.

## Density

- Touch targets ≥ 44px on mobile.
- Productivity surfaces use 8px grid; metaverse uses 16px pixel grid.

## Accessibility (non-negotiable)

- WCAG 2.2 AA.
- All interactive elements keyboard-reachable.
- Focus ring always visible (no `outline: none` without replacement).
- All images carry `alt` text (or `alt=""` for decorative).
- Soundscapes module: visual transcript or volume indicator equivalence.

## Whitespace

Use it. Crowded UIs are a productivity tool's most common failure.

## When Tempted To Break A Rule

Open an ADR. Don't slip a one-off into a PR.
