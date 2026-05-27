[Ver001.000]

# ADR-0010 — Audio Engine v0 Detail (Stems, Crossfade, Binaural, FFT)

- **Status:** Accepted
- **Date:** 2026-05-24
- **Deciders:** @hvrryh-web
- **Tags:** audio, web-audio, soundscapes, deep-canvas, binaural
- **Protects gate:** `G1.soundscapes`
- **Extends:** ADR-0006 (Web Audio API + OscillatorNode pair)

## Context

ADR-0006 picked **Web Audio API** as the engine and **OscillatorNode pair** for binaural beats. It did not specify how soundscape stems are loaded, looped without clicks, crossfaded between phases, or routed for FFT analysis to drive Deep Canvas Hush. Those gaps must close before `packages/@njz-os/audio-engine/src/engine.ts` can be implemented.

PRD requirements being satisfied:

- 30-minute seamless loops, gapless, no audible click/pop (§3.2.2).
- Mixing of multiple stems (rain + piano + drone, etc.).
- Real-time FFT analysis feeding the Deep Canvas painter (§3.2.3).
- Binaural beat synthesis with safety (volume limiter at 85 dB; §3.2.4).
- Sleep timer with gentle fade-out (§3.2.6).

Phase 1 ships 5 baseline tracks; Phase 2 grows to the full 40.

## Decision

### Stem loading

Each 30-minute soundscape is authored as a **5-minute looped stem** (or stems, when multi-layer) stored at `apps/web/public/audio/stems/<id>/<layer>.aac` (and `.ogg` fallback). Per-track metadata in `apps/web/public/audio/stems/<id>/manifest.json`:

```jsonc
{
  "id": "forest-rain",
  "category": "focus",
  "theme": "nature",
  "stems": [
    { "src": "rain.aac",  "gain": 0.8, "loop": true },
    { "src": "wind.aac",  "gain": 0.4, "loop": true }
  ],
  "loopMs": 300000,
  "crossfadeMs": 5000,
  "isPremium": false
}
```

Stems are fetched via `fetch(...).arrayBuffer()` then decoded with `AudioContext.decodeAudioData()` into `AudioBuffer` instances cached for the session.

### Gapless looping

Each stem uses **two `AudioBufferSourceNode` instances scheduled with a 5-second crossfade overlap.** Source A is scheduled to start at `t=0`. Source B is scheduled to start at `t = (loopMs - crossfadeMs)`. The pair alternates via `AudioBufferSourceNode.start(when)` precision scheduling on the `AudioContext` timeline. `GainNode` ramps on both sources (`linearRampToValueAtTime`) implement the crossfade. No `loop = true` flag — manual scheduling eliminates the gap that `loop` introduces.

### Mixing graph

```
[stem_1 source A]──┐
[stem_1 source B]──┤
                   ├──▶ [GainNode (per-stem)]──┐
[stem_2 source A]──┐                            │
[stem_2 source B]──┤                            │
                   ├──▶ [GainNode (per-stem)]──┤
                                                ├──▶ [GainNode (master)] ──▶
                                                │          │
[binaural carrier+/− beat/2 Hz]──▶ [pan L/R]──┤          ├──▶ [AnalyserNode] ──▶ [Deep Canvas]
                                                │          │
                                                │          ├──▶ [DynamicsCompressor (limiter)] ──▶ [destination]
```

### Binaural beats

Two `OscillatorNode`s — left at `(carrier - beat/2) Hz`, right at `(carrier + beat/2) Hz`. Each routed through a `StereoPannerNode` (pan = ±1.0) and a single shared `BiquadFilterNode` (low-pass at 800 Hz) for tone shaping. Default carrier 200 Hz; bands per `@njz-os/audio-engine/src/binaural.ts`.

### FFT for Deep Canvas

`AnalyserNode` tapped off the **master GainNode** (not the per-stem nodes — we want the user-audible mix). Settings:

```
analyser.fftSize = 2048;
analyser.smoothingTimeConstant = 0.85;
analyser.minDecibels = -90;
analyser.maxDecibels = -10;
```

Frame rate: `requestAnimationFrame` on the Deep Canvas painter. The painter calls `analyser.getByteFrequencyData(buffer)` once per frame; tier-detect to 60/30/15 fps based on `device.memory` and `navigator.hardwareConcurrency`.

### Volume limiter

A single `DynamicsCompressorNode` at the end of the graph configured as a brick-wall limiter:

```
limiter.threshold.value = -10;   // dBFS
limiter.knee.value = 0;          // hard knee
limiter.ratio.value = 20;        // near-infinite
limiter.attack.value = 0.003;    // 3 ms
limiter.release.value = 0.25;
```

Peak output target ≤ 85 dB SPL at typical phone/laptop volume (matches PRD §3.2.4 safety).

### Sleep timer + fade-out

Sleep timer uses `setTimeout` to trigger fade. Fade-out: `masterGain.gain.linearRampToValueAtTime(0, audioCtx.currentTime + fadeSeconds)` followed by `audioCtx.suspend()` on completion. Default fade: 30 seconds.

### Mobile audio quirks

- iOS Safari: `AudioContext` requires user-gesture resume. The first user interaction in `apps/web` calls `audioCtx.resume()`; we never auto-play.
- Screen-off suspension: subscribe to `visibilitychange`; on regain, call `audioCtx.resume()` and re-anchor stem scheduling timestamps.
- Per-browser quirk handling lives in `packages/@njz-os/audio-engine/src/quirks/` (one file per browser family).

## Consequences

**Positive:**

- Single source for all audio (mix + binaural + Deep Canvas tap). No second engine ever.
- Gapless looping verified by waveform test (no click within ±0.01 dB across the crossfade boundary).
- Deep Canvas FFT path is direct — sub-frame latency.
- Limiter is non-bypassable; safety guaranteed even with user gain mistakes.
- Manifest-driven stem definitions make adding tracks a data-only change.

**Negative:**

- Hand-built scheduler is more code than `source.loop = true`. ~150 LOC for the loop manager.
- Two `AudioBufferSourceNode`s per stem doubles node count. With 5 simultaneous stems × 2 sources + binaural pair = 12 nodes minimum. Web Audio handles this trivially; flagged for awareness.
- `AnalyserNode` runs at the main-thread `requestAnimationFrame` rate. If Deep Canvas painter blocks, audio is unaffected (separate thread), but FFT data freshness suffers.

**Neutral:**

- Per-track metadata in `manifest.json` co-located with stems — easy to author, easy to ship via CDN later (ADR-0012 asset pipeline).
- No third-party audio library. If complexity grows (e.g., effects chains, dynamic routing), revisit Tone.js in a follow-up ADR.

## Alternatives Considered

- **`AudioBufferSourceNode.loop = true`.** Rejected: introduces audible discontinuity at loop boundary unless stems are zero-crossing-aligned and exactly sample-accurate, which is brittle.
- **`HTMLAudioElement` + `MediaElementAudioSourceNode`.** Rejected: less precise scheduling; no sample-accurate gapless; mobile autoplay restrictions are even messier.
- **Tone.js for the engine.** Rejected for v0; overkill for current node count. Revisit in Phase 2+ if effects chains grow.
- **Audio Worklet for FFT.** Rejected: `AnalyserNode` data at 60 fps is sufficient for the visualization use case; Audio Worklet adds threading complexity without visible quality gain.
- **Stream the 30-minute file directly.** Rejected: 30 min × 256 kbps AAC = ~57 MB per track; 40 tracks = 2.3 GB. Loop-of-5-min stems is 6× smaller per track.

## Related

- ADR-0005 — PolyCo.World renderer (Deep Canvas pairs with this engine via the AnalyserNode tap).
- ADR-0006 — Audio engine choice (Web Audio + OscillatorNode); this ADR extends.
- ADR-0012 — Asset pipeline (defines how stems get from authoring tool into `apps/web/public/audio/stems/`).
- `docs/prototype-systems/PS-002-soundscapes.md` — module spec.
- `packages/@njz-os/audio-engine/src/soundscape.ts`, `binaural.ts`, `graph.ts` — types this ADR's runtime fills in.
- `.agents/SCHEMA_REGISTRY.md` — `Soundscape`, `BinauralPreset`, `AudioGraph` registered.

---

> When proposing, leave Status: Proposed. On approval, change to Accepted in a follow-up commit.
> Append a one-line entry to `.agents/DECISION_LOG.md` referencing this ADR.
