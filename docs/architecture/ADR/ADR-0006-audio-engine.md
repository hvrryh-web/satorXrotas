[Ver001.000]

# ADR-0006 — Audio Engine: Web Audio API + OscillatorNode Pair

- **Status:** Accepted
- **Date:** 2026-05-24
- **Deciders:** @hvrryh-web
- **Tags:** audio, soundscapes, binaural

## Context

The Soundscapes module needs:

- Gapless ambient track playback (30-min loops without click/pop).
- Mixing of multiple stems (e.g. rain + piano + low-frequency drone).
- Real-time FFT analysis to drive *Deep Canvas Hush* visualization.
- Binaural beat synthesis (carrier + beat frequency, stereo separation).
- Volume limiter (capped at 85 dB).
- Sleep timer with gentle fade-out.

Phase 1 ships 5 baseline tracks; Phase 2 grows to the full 40.

## Decision

Use the native **Web Audio API** as the engine. Specifically:

- **Soundscapes:** load 5-minute stems as `AudioBuffer`s; loop seamlessly via two scheduled `AudioBufferSourceNode`s with crossfade (5-second overlap). Mix stems through a `GainNode` graph.
- **Binaural beats:** two `OscillatorNode`s (carrier ± beat/2 Hz) routed through left and right `StereoPannerNode`s. Single `BiquadFilterNode` at 800 Hz low-pass for tone shaping.
- **FFT analysis:** `AnalyserNode` (`fftSize: 2048`) tapped off the master mix bus; feeds the Deep Canvas renderer via `getByteFrequencyData` at 60 fps.
- **Limiter:** `DynamicsCompressorNode` configured as a brick-wall limiter (`threshold: -10 dBFS`, `ratio: 20`).
- **Fade-out:** linear `gainNode.gain.linearRampToValueAtTime` over the configured duration.

No third-party audio library in Phase 1. If the engine grows complex enough to need one (e.g. Tone.js), open a follow-up ADR.

## Consequences

**Positive:**

- Web Audio API is universal, mature, zero-dependency, and small.
- Direct `AnalyserNode` tap into Deep Canvas keeps latency tight.
- Full client-side stack: no audio server cost.
- Hot-swap stems with no playback interruption.

**Negative:**

- Web Audio has documented quirks across browsers (Safari resume policies, mobile auto-suspend on screen-off). Mitigation: explicit resume on user gesture; visibility-API handler.
- Gapless looping requires careful scheduling. Mitigation: tested cross-fade strategy with `start(when)` precision.
- Binaural beats labelled "effects vary; not a medical treatment" in UI (per PRD §3.2.4).

**Neutral:**

- No third-party library means we own the bugs. Trade-off accepted at v0 complexity level.

## Alternatives Considered

- **Tone.js.** Considered; overkill for v0 needs; adds bundle. Revisit if synthesis needs grow.
- **Howler.js.** Considered; focused on game audio; doesn't expose AnalyserNode cleanly for FFT.
- **HTMLAudioElement only.** Rejected: no FFT, no mixing, no precise scheduling.
- **WebAudio + custom Worklet.** Considered for FFT but overkill for our 60-fps draw target; AnalyserNode suffices.

## Related

- `docs/prototype-systems/PS-002-soundscapes.md`
- `docs/product/PRD.md` §3.2 (referencing Endel, Brain.fm, Calm)
- ADR-0005 (PolyCo.World renderer — Deep Canvas Hush bridges audio + canvas)
