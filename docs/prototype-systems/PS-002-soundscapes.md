[Ver001.000]

# PS-002 — Soundscapes & Frequencies

- **Status:** Draft (Phase 0); flips to Approved when ADR-0008 lands.
- **Owner:** Implementer (Phase 1)
- **Phase:** 1 (5 baseline tracks) → 2 (full 40 + Deep Canvas advanced themes)
- **Package:** `@njz-os/audio-engine`
- **Gate:** `G1.soundscapes`

## Purpose

Ambient audio environments + binaural beats + the signature *Deep Canvas Hush* visualization. Differentiates RAT-OS against Endel / Brain.fm / Calm by pairing premium audio with generative visual storytelling.

## Surface

```ts
import { createAudioEngine, type Soundscape, type BinauralPreset } from '@njz-os/audio-engine';

const engine = createAudioEngine({ context: new AudioContext() });
await engine.playSoundscape('forest-rain');
await engine.playBinaural({ carrier: 200, beat: 10 }); // Alpha
const analyser = engine.getAnalyser(); // for Deep Canvas FFT
```

UI surface in `apps/web`:

- `/sound` — module home with category tiles (Focus / Relax / Sleep / Meditate).
- `/sound/active` — Deep Canvas full-screen player.
- `/sound/library` — saved sessions + Deep Canvas gallery.

## Domain Types

- `Soundscape`, `BinauralPreset`, `AudioGraph` (see SCHEMA_REGISTRY).

## Integration Points

- **Focus Hero:** "Focus Now" button bundles soundscape + focus timer.
- **PolyCo.World:** active soundscape lights up corresponding Home module room.
- **Vaultbrain:** persist favorites, custom presets, Deep Canvas gallery (PNG blobs).
- **Analytics:** session events feed cross-module correlation (which soundscapes correlate with which productivity outcomes).

## Risks

- **Mobile audio suspension on screen-off.** iOS Safari aggressively suspends `AudioContext`. Mitigation: `audioSession` API where available; explicit resume on visibility regain.
- **Track licensing.** Per `$0` budget, all tracks must be original or CC-licensed. Mitigation: in-house production + Freesound CC-licensed sources, attributed in app.
- **Binaural beats science claims.** Mixed evidence. Mitigation: clear "effects vary; not a medical treatment" labeling per PRD §3.2.4.
- **Deep Canvas perf on low-end mobile.** FFT @ 60 fps + paint can drop frames. Mitigation: tiered render (60/30/15 fps) by device capability detection.

## Verification

- Unit tests: gapless loop produces no audible click (waveform analysis in test).
- Unit tests: binaural carrier ± beat / 2 Hz panning correctness.
- Manual: 30-min loop on iPhone 12 (mid-range baseline) without dropouts.
- E2E: Deep Canvas session saves a non-empty PNG to user gallery.

## Out of Scope (Phase 1)

- AI-generated adaptive soundscapes (Endel-style real-time generation) — Phase 4.
- Voice prompts for guided meditation — Phase 2.
- Sleep cycle detection / smart wake — Phase 4+.
- Spatial audio / head-tracked binaural — Phase 5+.

## References

- PRD §3.2.
- ADR-0006 (audio engine choice).
- ADR-0005 (Deep Canvas rendering — depends on polyworld renderer pattern).
- ADR-0008 (audio engine extended — TBD).
