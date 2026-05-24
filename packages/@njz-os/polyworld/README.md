# @njz-os/polyworld

PolyCo.World scene primitives + renderer-agnostic API. Two backends planned: Canvas 2D (v0) and WebGL via pixi.js (v1).

## Surface (Phase 0 stubs)

- `tile` — `Tile`, `TileGrid`
- `decoration` — `Decoration` (placed item with unlock attribution)
- `actor` — `Actor`, `ActorStats`
- `scene` — `Scene`, `SceneKind`

## Phase 1 Implementation

Canvas 2D isometric renderer. Office scene only. See `docs/prototype-systems/PS-007-polyco-world.md` and ADR-0005.
