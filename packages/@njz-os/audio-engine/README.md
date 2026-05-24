# @njz-os/audio-engine

Web Audio-based soundscape playback, binaural beat synthesis, FFT taps for Deep Canvas Hush.

## Surface (Phase 0 stubs)

- `soundscape` — `Soundscape`, categories, themes
- `binaural` — `BinauralPreset`, frequency bands, range constants
- `graph` — declarative `AudioGraph` descriptor

## Phase 1 Implementation

`AudioContext`-based engine. Gapless stem loops with crossfade. OscillatorNode pair for binaural beats. `AnalyserNode` exposed for Deep Canvas FFT.

See `docs/prototype-systems/PS-002-soundscapes.md` and ADR-0006.
