[Ver001.000]

# ADR-0005 — PolyCo.World Renderer: HTML5 Canvas 2D for v0

- **Status:** Accepted
- **Date:** 2026-05-24
- **Deciders:** @hvrryh-web
- **Tags:** rendering, polyworld, performance

## Context

PolyCo.World is a cozy pixel-art isometric metaverse. Phase 1 ships only the Office shell — a small explorable scene with a few decorations and one hero sprite. Phase 2 expands to Office + Home with more decorations and animation. Phase 3 introduces multi-user (friend visits).

Rendering technology choices affect: development velocity, mobile performance, bundle size, and the path to richer effects later.

## Decision

- **v0 (Phase 1):** HTML5 Canvas 2D. Single render loop with `requestAnimationFrame`. Pixel-art sprites drawn via `drawImage`. Isometric projection via simple matrix transforms.
- **v1 (Phase 2+, behind feature flag):** WebGL via `pixi.js` for richer effects (particles for "Neural Dust" rewards, shaders for glow on streak milestones).
- **v2 (Phase 3+, behind separate ADR):** evaluate Three.js if 3D becomes desirable (e.g. for camera tilt during friend visits).

`@njz-os/polyworld` exposes a renderer-agnostic scene API. The Canvas 2D and WebGL implementations are swappable backends.

## Consequences

**Positive:**

- Canvas 2D has the smallest bundle, the broadest mobile support, and the simplest debug story.
- The renderer-agnostic API protects modules from backend changes.
- Feature-flagging WebGL lets us A/B perf before defaulting.

**Negative:**

- Canvas 2D peaks early on FX richness. Particle systems and shaders are awkward without WebGL.
- Two code paths once WebGL ships. Mitigation: shared scene-graph; backend-specific draw calls only.

**Neutral:**

- Pixel-art rendering doesn't care about backend — both Canvas 2D and WebGL handle nearest-neighbor scaling fine.

## Alternatives Considered

- **WebGL via pixi.js from day one.** Rejected for v0: more dependency surface, harder mobile debug, overkill for Phase 1 scene complexity.
- **Three.js from day one.** Rejected: 3D is not needed for v0; cost is real (bundle + learning curve).
- **DOM + CSS transforms.** Rejected: animation jitter on mobile; awkward for >50 sprites.
- **Phaser.** Considered; Canvas 2D is simpler and Phaser would be a third game-engine abstraction we don't yet need.

## Related

- ADR-0001 (Monorepo structure — `@njz-os/polyworld` placement)
- `docs/prototype-systems/PS-007-polyco-world.md`
