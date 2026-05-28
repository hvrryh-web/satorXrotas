[Ver001.000]

# Soundscapes + Deep Canvas Hush — Expanded Module Documentation

> **Lane B** in Stage 3 of the next-stages plan. Implementation-ready spec
> for the next agent picking up this lane.

## 1. Module identity & scope

| Field | Value |
|-------|-------|
| **Module name** | Soundscapes & Frequencies (with Deep Canvas Hush) |
| **Slug (code)** | `soundscapes` |
| **Status** | Documented (Accepted); implementation pending |
| **Owner role** | Implementer + Designer |
| **Channel** | `packages-engines` + `web-app` |
| **Gate protected** | `G1.soundscapes` (currently LOCKED) |
| **Phase** | 1 (5 baseline tracks) → 2 (full 40 + Deep Canvas advanced themes) |
| **Source ADRs** | ADR-0006 (Audio engine baseline) + ADR-0010 (v0 detail) |
| **Source PS** | `docs/prototype-systems/PS-002-soundscapes.md` |
| **Parent docs** | PRD §3.2, ROOT_AXIOMS PR-02 (design stance), PR-01 (engineering ethos) |
| **Plan reference** | Lane B in `.agents/session-workplans/SW-20260524-stage-3-lanes.md` |

Soundscapes is the **audio differentiator**. Where Endel ships AI-adaptive
audio and Brain.fm ships science-backed functional music, RAT-OS ships
**audio + visual storytelling** — the *Deep Canvas Hush* generative
canvas that "paints" itself over a session, driven by real-time FFT of
the user's audio mix. The PS-002 risk register flags this as a market
whitespace; ADR-0010 commits the technical path.

The implementation must satisfy four structural properties:

1. **Gapless looping.** 30-min soundscapes are constructed from 5-min
   stems with dual-`AudioBufferSourceNode` scheduling and a 5-second
   crossfade. Waveform tests verify ≤ 0.5 dB jump at the loop boundary.
2. **Real binaural beats.** Two `OscillatorNode`s at `carrier ± beat/2`
   Hz routed through `StereoPannerNode` L/R; a single shared 800 Hz
   low-pass `BiquadFilterNode` shapes tone.
3. **Deep Canvas Hush at 60/30/15 fps tier.** `AnalyserNode` tapped off
   the master `GainNode` feeds the painter; device-capability tier
   detection adapts frame rate so low-end mobile still ships.
4. **Hard volume limiter at 85 dB SPL.** Brick-wall
   `DynamicsCompressorNode` (threshold -10 dBFS, ratio 20, attack 3 ms)
   is non-bypassable; safety guaranteed even with user gain mistakes.

## 2. Architecture

```
apps/web/src/modules/soundscapes/
  ├─ SoundRoute.tsx        ─┐  Routes (was PhaseStub)
  ├─ Home.tsx              ─┘
  ├─ Active.tsx
  ├─ Gallery.tsx           Deep Canvas artwork gallery (vaultbrain-stored)
  └─ components/
       ├─ CategoryTile.tsx
       ├─ PlayerControls.tsx
       ├─ FrequencyChooser.tsx
       └─ DeepCanvasFullscreen.tsx
                 │
                 │ consumes via createAudioEngine()
                 ▼
packages/@njz-os/audio-engine/src/
  ├─ engine.ts             Master AudioGraph factory
  ├─ scheduler.ts          Dual-source crossfade looper
  ├─ manifest.ts           Zod-validated manifest parser
  ├─ binaural.ts           (extends stub) Oscillator pair + panner
  ├─ deep-canvas.ts        FFT-driven painter
  ├─ limiter.ts            DynamicsCompressorNode brick-wall
  ├─ soundscape.ts         (existing) types
  ├─ graph.ts              (existing) declarative AudioGraph
  └─ quirks/
       ├─ ios.ts            visibility-change resume + AudioSession API
       └─ android.ts        background-throttle workarounds
                 │
                 │ pulls manifests + stems from
                 ▼
apps/web/public/audio/stems/<id>/
  ├─ manifest.json
  ├─ <layer-1>.aac + <layer-1>.ogg
  └─ <layer-2>.aac + <layer-2>.ogg
```

Audio graph topology (canonical — `engine.ts` builds this):

```
[stem_1 source A]──┐
[stem_1 source B]──┤
                   ├──▶ [GainNode (stem 1)]──┐
[stem_2 source A]──┐                          │
[stem_2 source B]──┤                          │
                   ├──▶ [GainNode (stem 2)]──┤
                                              ├──▶ [GainNode (master)]──▶ [AnalyserNode (Deep Canvas tap)]
                                              │           │
[binaural carrier+/−beat/2 Hz]──▶ [pan L/R]──┤           ├──▶ [DynamicsCompressor (limiter)]──▶ [destination]
```

Key trade-offs already decided (ADR-0010 §"Decision"):

- Dual-`AudioBufferSourceNode` + manual `start(when)` scheduling beats
  `source.loop = true` (which introduces an audible discontinuity).
- `AnalyserNode` taps off the **master** GainNode (not per-stem) so the
  user-audible mix drives the visuals.
- No third-party audio library — Web Audio API direct keeps bundle
  minimal; Tone.js revisited only if Phase 2+ complexity demands it.

Architecture extensions for implementation (not in ADR):

- Per-platform `quirks/` directory addresses iOS Safari `AudioContext`
  suspension on screen-off and Android background-throttle behavior.
  Each is a small file that mounts a `visibilitychange` handler and
  optional `mediaSession` integration.
- Deep Canvas painter renders to an OffscreenCanvas (when supported) for
  thread-safe frame composition; falls back to main-thread canvas on
  older browsers.

## 3. Domain types & contracts

### Soundscape manifest (per-track)

```jsonc
// apps/web/public/audio/stems/forest-rain/manifest.json
{
  "id": "forest-rain",
  "category": "focus",
  "theme": "nature",
  "stems": [
    { "src": "rain.aac",  "ogg": "rain.ogg",  "gain": 0.8, "loop": true },
    { "src": "wind.aac",  "ogg": "wind.ogg",  "gain": 0.4, "loop": true }
  ],
  "loopMs": 300000,
  "crossfadeMs": 5000,
  "isPremium": false,
  "license": "CC-BY-4.0 / original",
  "credits": "..."
}
```

Validated via Zod:

```ts
// packages/@njz-os/audio-engine/src/manifest.ts
import { z } from 'zod';

export const StemSchema = z.object({
  src: z.string().endsWith('.aac'),
  ogg: z.string().endsWith('.ogg').optional(),
  gain: z.number().min(0).max(1),
  loop: z.boolean(),
});

export const SoundscapeManifestSchema = z.object({
  id: z.string(),
  category: z.enum(['focus', 'relax', 'sleep', 'meditate']),
  theme: z.enum(['nature', 'urban', 'cosmic', 'minimal', 'instrumental']),
  stems: z.array(StemSchema).min(1).max(4),
  loopMs: z.number().int().min(60_000).max(600_000),
  crossfadeMs: z.number().int().min(1_000).max(15_000),
  isPremium: z.boolean(),
  license: z.string(),
  credits: z.string().optional(),
});

export type SoundscapeManifest = z.infer<typeof SoundscapeManifestSchema>;
```

### Audio engine surface

```ts
// packages/@njz-os/audio-engine/src/engine.ts (new)
export interface AudioEngine {
  loadSoundscape(id: string): Promise<LoadedSoundscape>;
  playSoundscape(id: string): Promise<PlayHandle>;
  playBinaural(preset: BinauralPreset): PlayHandle;
  getAnalyser(): AnalyserNode;
  setMasterGain(value: number): void;
  setSleepTimer(durationSeconds: number): void;
  suspend(): Promise<void>;
  resume(): Promise<void>;
}

export interface PlayHandle {
  stop(fadeMs?: number): Promise<void>;
  setGain(value: number): void;
}

export function createAudioEngine(opts: { audioContext: AudioContext }): AudioEngine;
```

### Deep Canvas surface

```ts
// packages/@njz-os/audio-engine/src/deep-canvas.ts (new)
export interface DeepCanvasOptions {
  analyser: AnalyserNode;
  canvas: HTMLCanvasElement | OffscreenCanvas;
  theme?: 'flowfield' | 'mandala' | 'inkwash' | 'starfield'; // v0 ships flowfield
  targetFps?: 60 | 30 | 15; // auto-detect by default
}

export interface DeepCanvas {
  start(): void;
  stop(): void;
  captureGallery(): Promise<Blob>; // PNG export at 1920x1080
}

export function createDeepCanvas(opts: DeepCanvasOptions): DeepCanvas;
```

### Binaural surface (extends existing stub)

```ts
// packages/@njz-os/audio-engine/src/binaural.ts (extend)
export interface BinauralRunner {
  start(): void;
  stop(): void;
  setBeatHz(hz: number): void;
  setCarrierHz(hz: number): void;
}

export function createBinaural(
  opts: { audioContext: AudioContext; preset: BinauralPreset; output: AudioNode }
): BinauralRunner;
```

### Vaultbrain integration

Deep Canvas exports (PNG blobs) are persisted via vaultbrain as user
gallery items. Soundscape favourites and custom presets persist via
vaultbrain key/value. Per ADR-0008 schema:

| Operation | Vaultbrain endpoint | When |
|-----------|---------------------|------|
| Save Deep Canvas artwork | `POST /users/{id}/gallery/canvas` | session end (Deep Canvas mode) |
| Get gallery | `GET /users/{id}/gallery/canvas?limit=20` | gallery view mount |
| Save favourite | `POST /users/{id}/favourites/soundscape` | star tap |
| List favourites | `GET /users/{id}/favourites/soundscape` | category Home mount |

These are Phase-1 endpoints not yet in `contracts/openapi/njz-rat-os.yaml`
— add to the OpenAPI surface in Task B7 or coordinate via Lane F.

## 4. Implementation walkthrough — task by task

### Task B1 — Scaffold the AudioGraph factory

```bash
pnpm --filter @njz-os/audio-engine add zod
```

Create `src/engine.ts` exporting `createAudioEngine({ audioContext })`.
Wire the canonical signal chain (see §2 graph). Add a unit test
asserting node count + topology (no shortcut paths, no extra nodes).

```ts
test('master signal chain topology', () => {
  const ac = new AudioContext();
  const engine = createAudioEngine({ audioContext: ac });
  // Assert AnalyserNode tapped off master (not per-stem)
  expect(engine.getAnalyser().context).toBe(ac);
});
```

Commit: `feat(audio): scaffold AudioGraph factory`.

### Task B2 — Stem loader + manifest parser

Add `src/manifest.ts` with the Zod schema. Add `src/loader.ts`:

```ts
export async function loadSoundscape(
  id: string,
  baseUrl = '/audio/stems'
): Promise<LoadedSoundscape> {
  const manifestRes = await fetch(`${baseUrl}/${id}/manifest.json`);
  const manifest = SoundscapeManifestSchema.parse(await manifestRes.json());

  const buffers = await Promise.all(
    manifest.stems.map(async (stem) => {
      const url = `${baseUrl}/${id}/${stem.src}`;
      try {
        const arrayBuf = await (await fetch(url)).arrayBuffer();
        return await audioContext.decodeAudioData(arrayBuf);
      } catch {
        // Firefox path — fall back to Ogg
        if (!stem.ogg) throw new Error(`No ogg fallback for ${url}`);
        const oggBuf = await (await fetch(`${baseUrl}/${id}/${stem.ogg}`)).arrayBuffer();
        return await audioContext.decodeAudioData(oggBuf);
      }
    })
  );

  return { manifest, buffers };
}
```

Unit test with msw-mocked `fetch` and an invalid manifest (should throw
ZodError with a clear path).

Commit: `feat(audio): stem loader + Zod-validated manifest parser`.

### Task B3 — Gapless crossfade scheduler

Add `src/scheduler.ts`:

```ts
export class CrossfadeLoop {
  private sources: AudioBufferSourceNode[] = [];
  private currentIndex = 0;

  constructor(
    private context: AudioContext,
    private buffer: AudioBuffer,
    private destination: AudioNode,
    private crossfadeMs: number
  ) {}

  start(): void {
    const now = this.context.currentTime;
    const dur = this.buffer.duration;
    const fade = this.crossfadeMs / 1000;

    // Schedule first 2 sources end-to-end with crossfade overlap.
    this.scheduleSourceAt(now);
    this.scheduleSourceAt(now + dur - fade);
    // Subsequent sources rescheduled on each source's onended.
  }

  private scheduleSourceAt(startAt: number): void {
    const source = this.context.createBufferSource();
    source.buffer = this.buffer;
    const gain = this.context.createGain();
    source.connect(gain).connect(this.destination);

    const fade = this.crossfadeMs / 1000;
    const dur = this.buffer.duration;

    gain.gain.setValueAtTime(0, startAt);
    gain.gain.linearRampToValueAtTime(1, startAt + fade);
    gain.gain.setValueAtTime(1, startAt + dur - fade);
    gain.gain.linearRampToValueAtTime(0, startAt + dur);

    source.start(startAt);
    source.onended = () => this.scheduleSourceAt(this.context.currentTime + dur - fade);
    this.sources.push(source);
  }

  stop(): void { this.sources.forEach(s => s.stop()); this.sources = []; }
}
```

Waveform test:

```ts
test('no >0.5 dB jump at loop boundary', async () => {
  const ac = new OfflineAudioContext({ length: 48_000 * 35, sampleRate: 48_000, numberOfChannels: 2 });
  const buffer = createSineBuffer(ac, 5); // 5 s sine wave
  new CrossfadeLoop(ac, buffer, ac.destination, 5000).start();
  const rendered = await ac.startRendering();
  const samples = rendered.getChannelData(0);
  // Inspect samples around 4.5 s ± 0.5 s (the crossfade window).
  const rmsBefore = rms(samples, 48_000 * 4, 48_000 * 4.5);
  const rmsAfter  = rms(samples, 48_000 * 5, 48_000 * 5.5);
  expect(Math.abs(20 * Math.log10(rmsAfter / rmsBefore))).toBeLessThan(0.5);
});
```

Commit: `feat(audio): dual-source gapless crossfade scheduler`.

### Task B4 — Binaural beat generator

Replace stub `binaural.ts` with the real implementation while preserving
existing exports (`bandRange`, `FrequencyBand`, `BinauralPreset`):

```ts
export function createBinaural({ audioContext, preset, output }: {
  audioContext: AudioContext;
  preset: BinauralPreset;
  output: AudioNode;
}): BinauralRunner {
  const left  = audioContext.createOscillator();
  const right = audioContext.createOscillator();
  left.frequency.value  = preset.carrierHz - preset.beatHz / 2;
  right.frequency.value = preset.carrierHz + preset.beatHz / 2;

  const panL = audioContext.createStereoPanner(); panL.pan.value = -1;
  const panR = audioContext.createStereoPanner(); panR.pan.value =  1;
  const lowpass = audioContext.createBiquadFilter(); lowpass.type = 'lowpass'; lowpass.frequency.value = 800;

  left.connect(panL).connect(lowpass);
  right.connect(panR).connect(lowpass);
  lowpass.connect(output);

  return {
    start: () => { left.start(); right.start(); },
    stop:  () => { left.stop();  right.stop();  },
    setBeatHz: (hz) => {
      left.frequency.value  = preset.carrierHz - hz / 2;
      right.frequency.value = preset.carrierHz + hz / 2;
    },
    setCarrierHz: (hz) => {
      left.frequency.value  = hz - preset.beatHz / 2;
      right.frequency.value = hz + preset.beatHz / 2;
    },
  };
}
```

The PRD §3.2.4 safety copy ("Effects vary by individual. Binaural beats
are not a medical treatment.") must appear in the UI in Task B7.

Commit: `feat(audio): real OscillatorNode-pair binaural generator`.

### Task B5 — Deep Canvas Hush painter

Add `src/deep-canvas.ts`. Phase-1 theme: **flowfield** — particles drift
through a vector field shaped by FFT bands; low frequencies create broad
strokes, high frequencies add fine detail.

```ts
export function createDeepCanvas({ analyser, canvas, targetFps }: DeepCanvasOptions): DeepCanvas {
  const ctx = canvas.getContext('2d')!;
  const buf = new Uint8Array(analyser.frequencyBinCount);
  const particles = initParticles(200);
  let raf = 0;
  let lastFrame = 0;

  const fps = targetFps ?? detectTier(); // 60/30/15

  const loop = (now: number) => {
    raf = requestAnimationFrame(loop);
    if (now - lastFrame < 1000 / fps) return;
    lastFrame = now;
    analyser.getByteFrequencyData(buf);
    paintFrame(ctx, buf, particles);
  };

  return {
    start: () => { raf = requestAnimationFrame(loop); },
    stop:  () => { cancelAnimationFrame(raf); },
    captureGallery: async () => new Promise<Blob>((resolve) => {
      (canvas as HTMLCanvasElement).toBlob((blob) => resolve(blob!), 'image/png');
    }),
  };
}

function detectTier(): 60 | 30 | 15 {
  const cores = navigator.hardwareConcurrency ?? 4;
  const mem = (navigator as any).deviceMemory ?? 4;
  if (cores >= 4 && mem >= 4) return 60;
  if (cores >= 2 && mem >= 2) return 30;
  return 15;
}
```

`paintFrame` is the visual engine — see Phase 2 work for additional
themes (`mandala`, `inkwash`, `starfield`).

Commit: `feat(audio): Deep Canvas Hush flowfield painter`.

### Task B6 — Safety + mobile quirks

Add `src/limiter.ts`:

```ts
export function createLimiter(context: AudioContext): DynamicsCompressorNode {
  const c = context.createDynamicsCompressor();
  c.threshold.value = -10;
  c.knee.value = 0;
  c.ratio.value = 20;
  c.attack.value = 0.003;
  c.release.value = 0.25;
  return c;
}
```

Wired into `engine.ts` as the final node before destination.

Add `src/quirks/ios.ts`:

```ts
export function installIosQuirks(audioContext: AudioContext): () => void {
  const onVisibility = () => {
    if (document.visibilityState === 'visible' && audioContext.state === 'suspended') {
      void audioContext.resume();
    }
  };
  document.addEventListener('visibilitychange', onVisibility);
  return () => document.removeEventListener('visibilitychange', onVisibility);
}
```

Sleep timer:

```ts
export function setSleepTimer(engine: AudioEngine, durationSeconds: number): void {
  setTimeout(() => {
    const master = engine._masterGain();
    const ctx = master.context as AudioContext;
    master.gain.linearRampToValueAtTime(0, ctx.currentTime + 30); // 30 s fade
    setTimeout(() => void ctx.suspend(), 30_000);
  }, durationSeconds * 1000);
}
```

Commit: `feat(audio): brick-wall limiter + iOS quirks + sleep timer fade`.

### Task B7 — Soundscapes module UI

Replace `SoundRoute.tsx` PhaseStub. Build `Home.tsx`:

```tsx
const CATEGORIES = ['focus', 'relax', 'sleep', 'meditate'] as const;

export function FocusRoute() {
  return (
    <section className="rat-page">
      <h1>Soundscapes</h1>
      <div className="sound-category-grid">
        {CATEGORIES.map((cat) => <CategoryTile key={cat} category={cat} />)}
      </div>
      <h2>Frequencies (Binaural)</h2>
      <FrequencyChooser />
      <p className="binaural-safety-copy">
        Effects vary by individual. Binaural beats are not a medical treatment.
      </p>
      <h2>Deep Canvas gallery</h2>
      <Gallery />
    </section>
  );
}
```

`Active.tsx` mounts the engine, calls `playSoundscape(id)`, shows track
info + Deep Canvas full-screen toggle. `Gallery.tsx` lists previously
saved canvas blobs (PNG thumbnails) loaded via vaultbrain.

Commit: `feat(web/sound): module UI — categories, player, gallery`.

### Task B8 — Tests + Lighthouse + gate flip (orchestrator only)

Tests roll up from B1-B7. Lighthouse perf ≥ 85 on `/sound` route.
Orchestrator flips the gate in a follow-up PR (Task A8 pattern).

## 5. Telemetry & analytics events

| Event `kind` | When | Payload | Notes |
|--------------|------|---------|-------|
| `sound.session.start` | `playSoundscape()` resolves | `{ soundscapeId, mode: 'focus' | 'relax' | ..., binaural?: { band } }` | not in canonical events file yet — add in Task B7 |
| `sound.session.end` | `stop()` or sleep-timer fade | `{ soundscapeId, durationMs, withDeepCanvas: boolean }` | |
| `deep-canvas.captured` | `captureGallery()` resolves | `{ soundscapeId, sizeBytes }` | |

These extend `contracts/events/progression-events.json` — coordinate
with Lane F to update the canonical event taxonomy when Task B7 lands.

OKR mapping (per `docs/product/OKRS.md`):

- **O1.1 KR1** (MAU) — `sound.session.start` is a strong DAU signal.
- **O2.1** (Phase 2 module engagement) — `withDeepCanvas: true` ratio
  is a quality metric tracked in Month 4 cohort.

## 6. Test plan

| Tier | Tooling | Target |
|------|---------|--------|
| Unit | Vitest + OfflineAudioContext | crossfade boundary ≤ 0.5 dB; limiter clamps at -10 dBFS; binaural carrier ± beat/2 Hz |
| Integration | Vitest + msw | manifest fetch + Zod validation; Ogg fallback on AAC decode error |
| E2E | Playwright | start soundscape → 60 s → stop → assert PNG saved (mocked vaultbrain) |
| Cross-browser | Playwright (Chromium, Firefox, WebKit) | AAC primary, Ogg fallback works |
| Mobile | manual iPhone 12 + mid-range Android | screen-off resume; no audio dropouts |
| a11y | axe + manual | category tiles keyboard-navigable; binaural safety copy readable |
| Perf | Lighthouse CI | ≥ 85 on `/sound` route; FFT pipeline at 60 fps on mid-range |

## 7. Accessibility plan

| Component | Requirement |
|-----------|-------------|
| `CategoryTile` | Keyboard focus + Enter to enter category |
| Player controls | `aria-label` on every transport button; current track announced via `aria-live` |
| Deep Canvas full-screen | Esc closes; `role="img" aria-label="Generative audio-reactive canvas"` |
| Binaural safety copy | Visually prominent, ≥ 4.5:1 contrast, screen-reader exposed |
| Reduced motion | Deep Canvas auto-pauses animation under `prefers-reduced-motion: reduce`; static frame shown |
| Volume controls | Slider with `aria-valuemin/max/now`; current dB level announced |
| Headphones recommendation | Surfaced when binaural starts ("Use headphones for binaural effects") |

## 8. Risk register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| iOS Safari `AudioContext` suspends on screen-off; audio cuts | H | M | `quirks/ios.ts` handles `visibilitychange`; manual smoke each Friday |
| AAC decode fails on Firefox; user hears silence | M | M | Ogg fallback in every manifest; loader auto-falls-back |
| Loop boundary clicks despite crossfade | M | M | Waveform test asserts ≤ 0.5 dB; PR-gated |
| Deep Canvas drops frames on low-end devices | M | L | Tier-detect to 30/15 fps; static fallback if even 15 fps fails |
| Track licensing — CC content used without attribution | M | H | `manifest.json` carries `license` + `credits`; CI validator enforces both fields present |
| Binaural beats induce headaches in sensitive users | L | M | Safety copy + opt-in only; epilepsy warning on Deep Canvas |
| Bundle size from manifest schemas + engine code | L | L | Tree-shake aggressively; `engine.ts` is ~8 KB minified |

## 9. Cross-lane handoffs

| Direction | What | Counterparty | Contract |
|-----------|------|--------------|----------|
| **Consumes** asset pipeline | Lane C builds AAC + Ogg stems via FFmpeg; ships under `public/audio/stems/` | Lane C ADR-0012 |
| **Emits** `Deep Canvas captured` PNG | Lane C's PolyCo Office can hang these as wall art (Phase 2 feature) | shared blob storage via vaultbrain |
| **Coupling** focus session | Lane A's `useFocusSession` can trigger `playSoundscape()` when user opts in | optional integration in `Active.tsx` |
| **Consumes** auth state | Lane E supplies `userId` for vaultbrain favourites + gallery | `useAuth().userId` |
| **Emits** session events | Lane F adds them to canonical event taxonomy | `contracts/events/progression-events.json` |

## 10. Out of scope

- AI-generated adaptive soundscapes (Endel-style) — Phase 4.
- Voice prompts for guided meditation — Phase 2.
- Sleep-cycle detection / smart wake — Phase 4+.
- Spatial audio / head-tracked binaural — Phase 5+.
- Tone.js or other heavyweight library — revisit only if engine surface grows past v0.
- Additional Deep Canvas themes (mandala, inkwash, starfield) — Phase 2.

## 11. Open questions / TODOs for implementation

| Question | Options | Recommended default | Decision owner |
|----------|---------|---------------------|-----------------|
| Where to ship 5 baseline tracks for Phase 1? | (a) original commissioned (b) CC-BY from Freesound (c) hybrid | (c) — 2 commissioned + 3 CC-BY, all licensed and attributed | Product + Designer |
| Should the engine auto-pause when user switches to a different module? | (a) yes (b) no, keep playing | (b) — soundscapes are background; user opts out via stop | Implementer |
| Deep Canvas theme variety in Phase 1 — flowfield only, or also mandala? | (a) flowfield only (b) two themes | (a) — flowfield is enough; add mandala in Phase 2 | Designer |
| Headphone detection (Web Audio MediaSession API)? | (a) detect + nudge (b) skip | (a) thin nudge — improves binaural UX | Implementer |
| Vaultbrain blob storage shape for PNG captures? | (a) base64 in JSON (b) presigned URL + R2 | (a) Phase 1 (small volume); (b) Phase 2 via ADR | Architect (micro-ADR before Phase 2) |
| Should `playSoundscape` auto-suspend if user navigates away from `/sound`? | (a) yes (b) no | (b) — let audio persist across modules | Implementer |

---

> **When implementing**, the canonical event taxonomy in `contracts/events/progression-events.json` must be extended in Task B7 to include `sound.session.start/.end` and `deep-canvas.captured` (Lane F coordinates). Do not duplicate event names elsewhere.

> **See also:** ADR-0006, ADR-0010, PS-002, `packages/@njz-os/audio-engine/src/{soundscape,binaural,graph}.ts`, ROOT_AXIOMS PR-02 (design stance — binaural copy).
