[Ver001.000]

# PS-007 — PolyCo.World

- **Status:** Draft (Phase 0)
- **Owner:** Implementer + Designer
- **Phase:** 1 (Office shell) → 2 (Home module + decoration system) → 3 (social: friend visits, collaborative focus, seasonal events) → 5 (creator economy)
- **Package:** `@njz-os/polyworld` (renderer + scene API) + `@njz-os/pixel-art` (asset helpers)
- **Gate:** `G1.polyworld-office`, `G2.polyworld-home`, `G3.social`

## Purpose

The connective tissue. PolyCo.World is the metaverse that makes RAT-OS more than a feature bundle. Cozy pixel-art isometric world that renders the user's real-world cognitive progress as an explorable space.

## Surface

```ts
import { createScene, addDecoration, type Scene, type Decoration } from '@njz-os/polyworld';

const office = createScene('office');
addDecoration(office, { kind: 'trophy', position: [4, 2], unlockedBy: 'streak_7d' });
office.mount(canvas);
```

UI in `apps/web`:

- `/world` — main view (Office or Home, swappable).
- `/world/visit/:friendId` — Phase 3 friend visit.
- `/world/gallery` — Deep Canvas artwork hung as wall art (Phase 2+).

## Domain Types

- `Scene`, `Decoration`, `Actor`, `Tile` (see SCHEMA_REGISTRY).

## Integration Points

- **Every other module.** PolyCo.World subscribes to `ProgressionEvent`s from focus, audio, blocker, writing, learning, training; each event can trigger a scene update.
- **Vaultbrain:** scene state snapshots; decoration unlock log.
- **Soundscapes:** active soundscape lights up the corresponding Home room.
- **Audio engine (Deep Canvas):** generated canvases hangable as Office or Home wall art.

## Risks

- **Visual coherence vs scope creep.** Pixel-art needs a consistent palette + tile size or it falls apart. Mitigation: tight `@njz-os/pixel-art` style guide + asset review.
- **Mobile perf.** 60 fps target on mid-range Android is the bar. Canvas 2D is fine for Phase 1 scope (small Office scene). Mitigation: capped sprite count; off-screen culling; tier render rate.
- **Asset pipeline cost.** Hand-pixeled assets are slow to produce. Mitigation: small initial set (~50 unique tiles + ~20 decorations for Phase 1); community contribution model in Phase 5.
- **Save-state divergence cross-device.** Two devices showing different decorations is confusing. Mitigation: vaultbrain authoritative; visual reconciliation on focus return.

## Verification

- Unit: scene serialize/deserialize round-trips losslessly.
- Unit: decoration unlock rules are pure functions of event log.
- Perf: 60 fps on iPhone 12 with a maxed-out Office scene.
- E2E: complete a focus session → see decoration animation within 1 second.

## Out of Scope

- 3D / camera tilt — Phase 5+ (separate ADR).
- Voice chat during friend visits — speculative.
- Real-money trading of decorations between users — never.
- User-generated decorations — Phase 5 creator economy.

## References

- PRD §1.2, §3 (per-module PolyCo.World integration sections).
- ADR-0005 (renderer choice).
- ADR-0010 (asset pipeline — TBD).
- Style references: Tsuki's Odyssey, Stardew Valley aesthetic.
