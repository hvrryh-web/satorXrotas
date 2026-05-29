[Ver001.000]

# PolyCo.World + Asset Pipeline — Expanded Module Documentation

> **Lane C** in Stage 3 of the next-stages plan. Implementation-ready spec.

## 1. Module identity & scope

| Field | Value |
|-------|-------|
| **Module name** | PolyCo.World (Office shell + Asset pipeline) |
| **Slug (code)** | `polyco-world` |
| **Status** | Documented (Accepted); implementation pending |
| **Owner role** | Implementer + Designer |
| **Channel** | `packages-engines` + `web-app` + `tools/assets/` |
| **Gate protected** | `G1.polyworld-office` (currently LOCKED) |
| **Phase** | 1 (Office shell + asset pipeline) → 2 (Home module + decoration system) → 3 (social, friend visits) |
| **Source ADRs** | ADR-0005 (Canvas 2D renderer) + ADR-0012 (asset pipeline) |
| **Source PS** | `docs/prototype-systems/PS-007-polyco-world.md` |
| **Parent docs** | PRD §1.2, §3 (per-module PolyCo integrations), ROOT_AXIOMS PR-02 (design stance: cozy + precise) |
| **Plan reference** | Lane C in `.agents/session-workplans/SW-20260524-stage-3-lanes.md` |

PolyCo.World is the **connective tissue** that turns RAT-OS from a
feature bundle into a living ecosystem. A cozy pixel-art isometric world
where real-world cognitive work materially expands a virtual space. The
Office module ships in Phase 1; the Home module ships in Phase 2; social
features (friend visits, seasonal events) in Phase 3.

Lane C owns both:

1. **The rendering surface** — Canvas 2D isometric renderer (per ADR-0005),
   scene loader, sprite-atlas loader, hero actor with idle / walk /
   celebrate animations, decoration overlay that subscribes to
   `ProgressionEvent`s.
2. **The asset pipeline** (per ADR-0012) — Aseprite source files →
   packed spritesheets + JSON metadata, FFmpeg loudnorm → AAC + Ogg
   stems, validator that catches orphans and oversize and palette
   violations.

The two are coupled — the Office scene is the first major consumer of
the pipeline, and Lane B (audio) depends on the same pipeline for stems.

Three structural properties:

1. **60 fps on mid-range mobile.** Canvas 2D + off-screen culling +
   dirty-rect optimisation. Manual smoke on iPhone 12 baseline. If 60
   isn't achievable, tier to 30 with documented degradation.
2. **Shared 32-colour palette enforced.** `assets/palettes/njz-os.gpl`.
   The validator blocks any spritesheet that introduces off-palette
   colours.
3. **Decoration unlocks are pure functions of the event log.**
   Reproducible from the user's `progression_events` stream — Office
   state is never stored separately; it's derived. This makes cross-
   device sync trivial.

## 2. Architecture

```
assets/                            (source files — not in public/)
  ├─ sources/
  │   ├─ sprites/
  │   │   ├─ hero.aseprite
  │   │   ├─ tiles-office.aseprite
  │   │   └─ decorations-office.aseprite
  │   └─ audio/
  │       └─ <id>/<layer>.wav
  └─ palettes/njz-os.gpl           (32-color shared palette)
                 │ build scripts
                 ▼
tools/assets/
  ├─ build-sprites.mjs             Aseprite CLI → packed PNG + JSON
  ├─ build-audio.mjs               FFmpeg loudnorm → AAC + Ogg
  ├─ build-manifests.mjs           Emits soundscape manifest.json (Lane B)
  └─ validate-assets.mjs           Orphan / size / reference / palette
                 │ writes
                 ▼
apps/web/public/
  ├─ sprites/<sheet>.png + .json
  └─ audio/stems/<id>/manifest.json + stems

                 │ loaded by
                 ▼
packages/@njz-os/pixel-art/src/
  └─ loader.ts                     Sprite-atlas loader; frame resolver

                 │ used by
                 ▼
packages/@njz-os/polyworld/src/
  ├─ render-canvas2d.ts            Renderer; mount / tick / unmount
  ├─ scene-loader.ts               Parses Scene JSON
  ├─ projection.ts                 16 px tile, 2:1 isometric math
  ├─ culling.ts                    Off-screen + dirty-rect
  ├─ scene.ts                      (existing) types
  ├─ tile.ts                       (existing) types
  ├─ actor.ts                      (existing) types
  └─ decoration.ts                 (existing) types

                 │ mounted by
                 ▼
apps/web/src/modules/polyco-world/
  ├─ WorldRoute.tsx                (was PhaseStub)
  ├─ Office.tsx                    Office scene mount
  └─ scenes/office.json            8×8 floor + hero at (4,4)
```

Trade-offs already decided:

- Canvas 2D (not WebGL) for v0 — smallest bundle, broadest mobile, ADR-0005.
- Aseprite (paid; LibreSprite acceptable) as authoring tool — single
  shared palette enforced.
- Per-build artefacts checked in (PNG + JSON) — reproducible from
  sources via `pnpm assets:build-sprites` etc.
- Phase 1 hosts assets from `apps/web/public/` (Vercel static) — R2
  migration deferred to Phase 2 per ADR-0012.

Architecture extensions for impl:

- **Renderer abstraction.** `render-canvas2d.ts` exposes `mount`, `tick`,
  `unmount` — same interface a future WebGL backend can implement,
  preserving the swappable-backend promise of ADR-0005.
- **Event-derived scene state.** A pure function
  `deriveSceneFromEvents(baseScene, events) -> Scene` lets us replay
  any decoration-unlock history and reproduce the user's Office
  deterministically. Used in tests + in the live mount.

## 3. Domain types & contracts

### Existing (from Phase 0 stubs)

`packages/@njz-os/polyworld/src/tile.ts`, `actor.ts`, `decoration.ts`,
`scene.ts` already define `Tile`, `Decoration`, `Actor`, `ActorStats`,
`Scene`, `SceneKind`. Lane C extends these only with renderer-internal
state types.

### Renderer surface

```ts
// packages/@njz-os/polyworld/src/render-canvas2d.ts
export interface Renderer {
  mount(canvas: HTMLCanvasElement, scene: Scene): void;
  tick(deltaMs: number): void;
  unmount(): void;
  applyEvent(event: ProgressionEvent): void; // decoration unlock derivation
}

export function createCanvas2DRenderer(opts: {
  assetLoader: SpriteAtlasLoader;
  decorationRules: DecorationUnlockRules;
}): Renderer;
```

### Scene-loader surface

```ts
// packages/@njz-os/polyworld/src/scene-loader.ts
export function loadScene(url: string): Promise<Scene>;
export function deriveSceneFromEvents(base: Scene, events: ProgressionEvent[]): Scene;
```

### Pixel-art loader surface (extends Phase 0 stubs)

```ts
// packages/@njz-os/pixel-art/src/loader.ts (new)
export interface SpriteAtlasLoader {
  load(sheetUrl: string): Promise<SpriteSheet>;
  frame(sheet: SpriteSheet, animationId: string, frameIndex: number): SpriteFrame;
}

export function createAtlasLoader(): SpriteAtlasLoader;
```

### Asset pipeline tool contracts

```ts
// tools/assets/validate-assets.mjs (exit non-zero on failure)
- Every spritesheet PNG referenced from any scene JSON exists in
  apps/web/public/sprites/.
- Every soundscape ID in @njz-os/audio-engine has manifest.json under
  apps/web/public/audio/stems/<id>/.
- Total apps/web/public/audio/ ≤ 200 MB.
- Total apps/web/public/sprites/ ≤ 5 MB.
- No off-palette pixels in any committed PNG (sampled).
- No orphan files (assets/sources/X.aseprite must have a corresponding
  apps/web/public/sprites/X.png).
```

### Decoration unlock rules

```ts
// packages/@njz-os/polyworld/src/decoration-rules.ts (new)
export interface DecorationUnlockRules {
  forModule(slug: ModuleSlug): UnlockRule[];
}

export interface UnlockRule {
  decorationId: string;
  trigger: 'xp_threshold' | 'streak_threshold' | 'session_count';
  threshold: number;
  position: [number, number]; // x, y in scene tile space
}
```

Phase 1 rules (Office scene):

| Decoration | Trigger | Threshold |
|------------|---------|-----------|
| `desk-trophy` | focus-hero XP | 100 |
| `coffee-mug` | focus-hero session count | 5 |
| `bookshelf-row-1` | focus-hero streak | 7 days |
| `plant-corner` | session count (any) | 10 |
| `framed-canvas-1` | soundscapes Deep Canvas capture count | 3 |

Phase 2 adds more decorations + the Home scene's full rule set.

## 4. Implementation walkthrough — task by task

### Task C1 — Asset pipeline scripts

`tools/assets/build-sprites.mjs`:

```js
#!/usr/bin/env node
import { execSync } from 'node:child_process';
import { readdirSync } from 'node:fs';
import { join } from 'node:path';

const SOURCES = 'assets/sources/sprites';
const OUT = 'apps/web/public/sprites';

for (const file of readdirSync(SOURCES).filter(f => f.endsWith('.aseprite'))) {
  const name = file.replace(/\.aseprite$/, '');
  execSync(
    `aseprite -b ${SOURCES}/${file} \
      --sheet ${OUT}/${name}.png \
      --data ${OUT}/${name}.json \
      --sheet-type packed \
      --format json-hash \
      --shape-padding 1`,
    { stdio: 'inherit' }
  );
}
```

`tools/assets/build-audio.mjs`:

```js
#!/usr/bin/env node
import { execSync } from 'node:child_process';
import { readdirSync, mkdirSync } from 'node:fs';

const SOURCES = 'assets/sources/audio';
const OUT = 'apps/web/public/audio/stems';

for (const id of readdirSync(SOURCES, { withFileTypes: true }).filter(d => d.isDirectory())) {
  const idDir = `${SOURCES}/${id.name}`;
  const outDir = `${OUT}/${id.name}`;
  mkdirSync(outDir, { recursive: true });
  for (const wav of readdirSync(idDir).filter(f => f.endsWith('.wav'))) {
    const name = wav.replace(/\.wav$/, '');
    execSync(`ffmpeg -y -i ${idDir}/${wav} -af loudnorm=I=-16:LRA=11:TP=-1.5 -c:a aac -b:a 256k ${outDir}/${name}.aac`, { stdio: 'inherit' });
    execSync(`ffmpeg -y -i ${idDir}/${wav} -af loudnorm=I=-16:LRA=11:TP=-1.5 -c:a libvorbis -q:a 6 ${outDir}/${name}.ogg`, { stdio: 'inherit' });
  }
}
```

`tools/assets/validate-assets.mjs`:

```js
#!/usr/bin/env node
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

let failures = 0;
const fail = (m) => { console.error('✗', m); failures += 1; };

// Total audio size check
const audioBytes = walkSize('apps/web/public/audio');
if (audioBytes > 200 * 1024 * 1024) fail(`public/audio exceeds 200 MB: ${audioBytes}`);

// Total sprites size check
const spriteBytes = walkSize('apps/web/public/sprites');
if (spriteBytes > 5 * 1024 * 1024) fail(`public/sprites exceeds 5 MB: ${spriteBytes}`);

// Each scene's referenced sprite exists
for (const sceneJson of findFiles('apps/web/src/modules', /\.scenes\/.*\.json$/)) {
  const scene = JSON.parse(readFileSync(sceneJson, 'utf8'));
  // Verify every sprite path exists
}

// Palette check — sample PNGs, ensure no off-palette pixels (Phase 2 — Phase 1 ships TODO)

if (failures > 0) { console.error(`\n${failures} asset validation failure(s).`); process.exit(1); }
```

Wire `pnpm assets:build-sprites`, `pnpm assets:build-audio`, `pnpm
assets:validate` in root `package.json`. Add `pnpm assets:validate` to
CI's `ci.yml` workflow.

Commit: `feat(assets): build + validate asset pipeline scripts`.

### Task C2 — Shared palette + seed asset set

Author `assets/palettes/njz-os.gpl` (GIMP palette format, 32 colors).
Cozy, low-saturation, with warm and cool family balance. Document
choices in a comment header. Reference from `ROOT_AXIOMS/01_PRINCIPLES/02-design-stance.md` (palette + tokens).

Produce minimum Phase-1 asset set:

| Asset | File | Notes |
|-------|------|-------|
| Floor tiles | `tiles-office-floor.aseprite` | 5 variants (light wood + plain) |
| Wall tiles | `tiles-office-wall.aseprite` | 5 variants |
| Door | `tiles-office-door.aseprite` | 1 + open/closed |
| Hero idle | `hero-idle.aseprite` | 4 frames @ 8 fps |
| Hero walk | `hero-walk.aseprite` | 8 frames @ 12 fps |
| Hero celebrate | `hero-celebrate.aseprite` | 6 frames |
| 5 baseline decorations | each its own `.aseprite` | desk, bookshelf, plant, coffee-mug, framed-canvas |

Run pipeline; commit generated PNGs + JSON.

Commit: `feat(assets): shared 32-color palette + seed Office asset set`.

### Task C3 — Pixel-art sprite loader

`packages/@njz-os/pixel-art/src/loader.ts`:

```ts
export interface SpriteSheet {
  image: HTMLImageElement;
  meta: SheetMeta;
}

interface SheetMeta {
  frames: Record<string, { frame: { x: number; y: number; w: number; h: number }; duration: number }>;
}

export function createAtlasLoader(): SpriteAtlasLoader {
  const cache = new Map<string, Promise<SpriteSheet>>();
  return {
    async load(sheetUrl) {
      if (cache.has(sheetUrl)) return cache.get(sheetUrl)!;
      const p = (async () => {
        const [imgRes, jsonRes] = await Promise.all([
          loadImage(sheetUrl),
          fetch(sheetUrl.replace(/\.png$/, '.json')).then(r => r.json()),
        ]);
        return { image: imgRes, meta: jsonRes };
      })();
      cache.set(sheetUrl, p);
      return p;
    },
    frame(sheet, animId, idx) {
      const key = `${animId}/${String(idx).padStart(2, '0')}`;
      const frame = sheet.meta.frames[key];
      if (!frame) throw new Error(`Frame ${key} not in ${sheet}`);
      return { sheetId: sheet, x: frame.frame.x, y: frame.frame.y, w: frame.frame.w, h: frame.frame.h, duration: frame.duration };
    },
  };
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((res, rej) => { const img = new Image(); img.onload = () => res(img); img.onerror = rej; img.src = src; });
}
```

Test against a fixture sheet committed in `test/fixtures/`.

Commit: `feat(pixel-art): sprite-atlas loader with caching`.

### Task C4 — Canvas 2D isometric renderer

`packages/@njz-os/polyworld/src/render-canvas2d.ts`:

```ts
const TILE_W = 16;
const TILE_H = 8;  // 2:1 isometric

function tileToScreen(x: number, y: number): [number, number] {
  return [(x - y) * TILE_W, (x + y) * TILE_H];
}

export function createCanvas2DRenderer(opts: {
  assetLoader: SpriteAtlasLoader;
  decorationRules: DecorationUnlockRules;
}): Renderer {
  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D;
  let scene: Scene;
  let raf = 0;
  let dirty = new Set<string>(); // tile keys that need redraw

  function paint() {
    if (dirty.size === 0) return;
    // Z-order by (x + y) for isometric depth
    const tiles = scene.tiles.flatMap((row, y) => row.map((tile, x) => ({ tile, x, y })))
      .filter(({ tile }) => tile !== null)
      .sort((a, b) => (a.x + a.y) - (b.x + b.y));
    for (const { tile, x, y } of tiles) {
      const [sx, sy] = tileToScreen(x, y);
      if (sx + TILE_W < 0 || sx > canvas.width) continue; // cull
      const sheet = /* resolve via assetLoader */;
      ctx.drawImage(sheet.image, /* frame rect */, sx, sy, TILE_W * 2, TILE_H * 4);
    }
    dirty.clear();
  }

  return {
    mount(_canvas, _scene) {
      canvas = _canvas; scene = _scene;
      ctx = canvas.getContext('2d')!;
      ctx.imageSmoothingEnabled = false; // pixel-art crisp
      const loop = () => { paint(); raf = requestAnimationFrame(loop); };
      raf = requestAnimationFrame(loop);
      // Mark whole scene dirty initially
      scene.tiles.forEach((row, y) => row.forEach((_, x) => dirty.add(`${x},${y}`)));
    },
    tick(_deltaMs) { /* advance hero animation frame, etc. */ },
    unmount() { cancelAnimationFrame(raf); },
    applyEvent(event) {
      // Apply decoration unlock if rules match
      const rules = opts.decorationRules.forModule(event.module);
      for (const rule of rules) {
        if (shouldUnlock(rule, event)) {
          scene.decorations.push({ /* ... */ });
          dirty.add(`${rule.position[0]},${rule.position[1]}`);
        }
      }
    },
  };
}
```

Perf test: 100 sprites @ 60 fps on a baseline laptop (Vitest perf-mode
tolerable; full check on iPhone 12 manual).

Commit: `feat(polyworld): Canvas 2D isometric renderer`.

### Task C5 — Scene graph + decoration system

`scene-loader.ts`:

```ts
export async function loadScene(url: string): Promise<Scene> {
  const res = await fetch(url);
  return SceneSchema.parse(await res.json());
}

export function deriveSceneFromEvents(base: Scene, events: ProgressionEvent[]): Scene {
  const rules = createDecorationRules();
  const decorations = [...base.decorations];
  for (const event of events) {
    for (const rule of rules.forModule(event.module)) {
      if (shouldUnlock(rule, event) && !decorations.some(d => d.id === rule.decorationId)) {
        decorations.push(materialise(rule));
      }
    }
  }
  return { ...base, decorations };
}
```

`decoration-rules.ts` — see §3 table. Hero actor: idle/walk/celebrate
animations cycle via `tick`.

Commit: `feat(polyworld): scene loader + decoration unlock rules`.

### Task C6 — Office scene + ProgressionEvent subscription

Author `apps/web/src/modules/polyco-world/scenes/office.json`:

```json
{
  "worldId": "default-office",
  "kind": "office",
  "size": [8, 8],
  "tiles": [/* 8×8 grid; floor in middle 6×6, walls on edge */],
  "decorations": [],
  "actors": [
    { "id": "hero", "kind": "hero", "spriteId": "hero-idle.png", "position": [4, 4], "facing": "s" }
  ]
}
```

Subscribe to vaultbrain `ProgressionEvent` stream (when adapter ready)
or poll `GET /users/{id}/progression` every 30 s (Phase 1 fallback
while adapter is NOT_IMPLEMENTED):

```tsx
function useProgressionEvents(userId: UserId): ProgressionEvent[] {
  const { data } = useQuery({
    queryKey: ['progression', userId],
    queryFn: () => vaultbrainClient.getProgression(userId),
    refetchInterval: 30_000,
  });
  return data?.events ?? [];
}
```

`Office.tsx` calls `deriveSceneFromEvents(baseOffice, events)` on mount
and on every event-stream update. New decorations animate in via a
small celebration over the target tile.

Commit: `feat(polyworld): Office scene + event-derived decoration system`.

### Task C7 — Module UI + tests + gate flip (orchestrator)

Replace `WorldRoute.tsx` PhaseStub with `Office.tsx` mount.

Tests:

- Scene round-trip (`loadScene` then `JSON.stringify` matches input)
- Decoration derivation: given canned `[session.complete] × 5`,
  expect `coffee-mug` to appear at its position.
- Renderer pixel-perfect snapshot at scene mount (no anti-aliasing).
- Mobile perf check manual on iPhone 12.

Commit: `feat(web/polyworld): Office route + tests`.

A8-style gate flip reserved for orchestrator.

## 5. Telemetry & analytics events

PolyCo.World is primarily a **consumer** of events, not an emitter.
However:

| Event | When | Payload |
|-------|------|---------|
| `polyworld.decoration.unlocked` | `applyEvent()` adds a new decoration | `{ userId, decorationId, fromEventKind, at }` |
| `polyworld.scene.viewed` | Office scene mounted | `{ userId, sceneId, durationMs }` |

Adds to `contracts/events/progression-events.json` in Lane F
coordination.

OKR mapping:

- **O1.1 KR1, KR2** — Office views are a daily engagement signal.
- PRD §2.3.2 module engagement target — "PolyCo.World 45% of DAU @
  Month 6" — measured via `polyworld.scene.viewed` cohort.

## 6. Test plan

| Tier | Tooling | Target |
|------|---------|--------|
| Unit | Vitest | scene round-trip; decoration derivation determinism; renderer culling |
| Unit | Vitest perf-mode | 100 sprites at 60 fps on Node simulation |
| Integration | Vitest | `loader.ts` against fixture sheets |
| E2E | Playwright | mount /world → see hero → mock progression event → see decoration appear |
| Mobile | manual iPhone 12 + mid-range Android | 60 fps; no jank on tile scroll |
| Asset pipeline | `pnpm assets:validate` in CI | no orphans; size budgets respected |
| Pixel-perfect | Playwright `toMatchSnapshot` with `imageSmoothingEnabled=false` | scene mounts identically across runs |

## 7. Accessibility plan

| Component | Requirement |
|-----------|-------------|
| Canvas | `role="img"` + dynamic `aria-label` describing the scene state ("Office with hero at desk, 3 decorations unlocked") |
| Hero | Click target ≥ 44×44 px; keyboard-focusable when canvas focused |
| Decoration unlock notification | `aria-live="polite"` toast: "Unlocked: coffee mug for completing 5 focus sessions" |
| Reduced motion | `prefers-reduced-motion: reduce` disables hero idle/walk animations; static frame shown |
| Color contrast | Decoration sprites against floor ≥ 3:1 contrast minimum |
| Alternative text view | Phase 2 — text-list "Your Office" surface for screen-reader-only users |

Phase 2 ships an accessible text view of the Office (list of decorations
with descriptions); Phase 1 ships the canvas + the aria-label summary.

## 8. Risk register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Visual coherence breaks across hand-authored assets | M | H | Shared 32-color palette enforced by validator; design review per PR |
| 60 fps unattainable on low-end Android | M | M | Tier-detect to 30 fps; documented degradation |
| Asset bundle size grows past Phase 1 budget | M | M | Validator enforces 200 MB audio / 5 MB sprite caps; PR-gated |
| Aseprite paid license blocks contributors | M | L | LibreSprite (FOSS fork) acceptable; documented in CONTRIBUTING |
| Decoration unlocks feel arbitrary to user | L | M | UI surfaces "What you unlocked" + the trigger; tooltip on hover |
| Cross-device "office state" desync (server has different decoration set than client) | M | L | Pure derivation from event log — server returns events, client derives. No conflict possible. |
| Hero animation drifts across devices | L | L | Time-based animation tick using `Date.now()`, not frame count |
| Decoration positions overlap walls or other decorations | M | L | Validation in scene loader: every decoration position must be on a `walkable: false` floor tile and not occupied |

## 9. Cross-lane handoffs

| Direction | What | Counterparty |
|-----------|------|--------------|
| **Consumes** ProgressionEvents from all lanes | Subscribes via vaultbrain to derive scene state | events from Lane A (focus.*), Lane B (sound.*), Lane D (blocker.*), Lane E (auth.*) |
| **Produces** asset pipeline | Lane B consumes the same pipeline for audio stems | tools/assets/* shared |
| **Consumes** auth state | userId for vaultbrain event-stream subscription | Lane E `useAuth()` |
| **Coordinates** event taxonomy | New event names for `polyworld.*` must land in `contracts/events/progression-events.json` | Lane F |

## 10. Out of scope (this module / phase)

- Home module (PS-007 §"Phase 2") — Phase 2.
- Friend visits, collaborative focus, public gallery — Phase 3.
- Real-money trading of decorations — never (per ROOT_AXIOMS PR-03).
- 3D / camera tilt — Phase 5+ (separate ADR).
- User-generated decorations (creator economy) — Phase 5.
- AI-generated pixel art — Phase 4+ evaluation (per ADR-0012 alternatives).
- WebGL backend — Phase 2+ (ADR-0005 leaves the door open).

## 11. Open questions / TODOs for implementation

| Question | Options | Recommended default | Decision owner |
|----------|---------|---------------------|-----------------|
| Where do we host the 32-color palette source-of-truth? | (a) `assets/palettes/njz-os.gpl` (b) inline TypeScript | (a) — Aseprite imports `.gpl` natively; CI validator reads same file | Designer |
| Should the renderer support a hot-reload during dev (HMR for scene JSON)? | (a) yes (b) no | (a) — small impl, big DX win | Implementer |
| How does the office react if vaultbrain is unreachable? | (a) show base scene (empty office) (b) show last-known cached scene | (b) — cache last successful response in localStorage; renders instantly | Implementer |
| Phase 1 asset count — what's the minimum viable Office? | enumerate seed set | per §C2 table | Designer |
| Asset size budgets — strict or warn? | (a) strict (CI fail) (b) warn-only | (a) strict on size; (b) warn-only on count | Platform |
| Decoration animations — entrance only, or persistent idle? | (a) entrance + idle (b) entrance only | (b) — Phase 1 keeps perf budget; idle in Phase 2 | Designer |

---

> **When implementing**, every PR that adds an asset must run
> `pnpm assets:validate` locally before push. The shared palette is
> non-negotiable — off-palette commits will be reverted.

> **See also:** ADR-0005, ADR-0012, PS-007, `contracts/events/progression-events.json`, `packages/@njz-os/polyworld/src/`, `packages/@njz-os/pixel-art/src/`, ROOT_AXIOMS PR-02 (design stance).
