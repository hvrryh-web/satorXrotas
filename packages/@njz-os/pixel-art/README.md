# @njz-os/pixel-art

Pixel-art rendering helpers shared by `@njz-os/polyworld` and any module rendering pixel sprites.

## Surface (Phase 0 stubs)

- `SpriteSheet` — atlas descriptor
- `SpriteFrame` — single frame reference
- `SpriteAnimation` — looped/one-shot animation

## Phase 1+

Nearest-neighbor scaling helpers, atlas loader, frame iterator, easing utilities.

## Asset Pipeline (Phase 2+, ADR-0010)

Decide: pre-baked Aseprite exports vs runtime atlas assembly. Decision deferred until first artist begins production.
