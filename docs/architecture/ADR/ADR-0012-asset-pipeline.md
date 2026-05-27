[Ver001.000]

# ADR-0012 — Asset Pipeline (Aseprite + FFmpeg → public/; R2 in Phase 2)

- **Status:** Accepted
- **Date:** 2026-05-24
- **Deciders:** @hvrryh-web
- **Tags:** assets, pixel-art, audio, aseprite, ffmpeg, cdn, polyworld, soundscapes
- **Protects gate:** `G1.polyworld-office` (alongside ADR-0005)

## Context

Phase 1 needs:

- Pixel-art assets for `@njz-os/polyworld` — ~50 baseline tiles + ~20 decorations + a hero sprite (idle + walk + celebrate animations), per PS-007.
- Audio stems for `@njz-os/audio-engine` — 5 baseline soundscapes (Forest Rain, Coffee Shop, Deep Space, White Noise, Lo-Fi Beats) × ~2 stems each = 10 stems, per ADR-0010.
- A repeatable, scriptable path from authoring tools to runtime artefacts.

Constraints from `docs/product/PRD.md` §1.4 and ROOT_AXIOMS PR-01: zero-budget for MVP; open-source first. Constraints from ADR-0010: stems must be 5-minute loops, normalised to a target loudness, in AAC (with Ogg fallback). Constraints from PS-007: pixel-art must use a single shared palette and consistent tile size (16 px) to maintain visual coherence.

We need an explicit pipeline so Designer/Implementer agents producing assets follow the same conventions, and so the asset surface is reproducible from sources.

## Decision

### Authoring tools

| Asset type | Source format | Authoring tool |
|------------|---------------|----------------|
| Pixel-art tiles | `.aseprite` (multi-layer, multi-frame) | Aseprite (paid; FOSS LibreSprite acceptable) |
| Pixel-art sprites (hero, NPCs) | `.aseprite` | Aseprite/LibreSprite |
| Audio stems | `.wav` (24-bit, 48 kHz) | Reaper, Audacity, or any DAW |
| Card illustrations | `.svg` or `.png` | Inkscape, Figma, hand-pixeled in Aseprite |

Source files live in `assets/sources/` (gitignored from public surfaces; tracked via Git LFS once they grow). Built artefacts live in `apps/web/public/`.

### Build pipeline (CLI scripts in `tools/assets/`)

```
tools/assets/
  build-sprites.mjs       Aseprite CLI → spritesheet PNG + JSON metadata
  build-audio.mjs         FFmpeg → AAC (256 kbps) + Ogg fallback (192 kbps); loudness-normalised
  build-manifests.mjs     Generate per-soundscape manifest.json
  validate-assets.mjs     CI guard: every referenced asset exists; no stale files
```

Invocations:

```bash
pnpm assets:build-sprites
pnpm assets:build-audio
pnpm assets:build-manifests
pnpm assets:validate           # CI runs this
```

### Sprite pipeline (Aseprite → JSON+PNG)

```bash
aseprite -b assets/sources/sprites/<name>.aseprite \
  --sheet apps/web/public/sprites/<name>.png \
  --data  apps/web/public/sprites/<name>.json \
  --sheet-type packed \
  --format json-hash \
  --shape-padding 1
```

- Output spritesheet PNG: nearest-neighbor friendly, 1-px shape padding to prevent texture bleeding.
- Output JSON: per-frame `{ x, y, w, h, duration }` records consumed by `packages/@njz-os/pixel-art` loader.
- One spritesheet per logical asset (one sheet per character; one sheet per tile category).
- Palette: shared 32-color palette in `assets/palettes/njz-os.gpl`; Aseprite enforces on save.

### Audio pipeline (FFmpeg → AAC + Ogg)

```bash
ffmpeg -i assets/sources/audio/<id>/<layer>.wav \
  -af "loudnorm=I=-16:LRA=11:TP=-1.5" \
  -c:a aac -b:a 256k apps/web/public/audio/stems/<id>/<layer>.aac

ffmpeg -i assets/sources/audio/<id>/<layer>.wav \
  -af "loudnorm=I=-16:LRA=11:TP=-1.5" \
  -c:a libvorbis -q:a 6 apps/web/public/audio/stems/<id>/<layer>.ogg
```

- Loudness target: −16 LUFS integrated (matches Apple/Spotify recommendations for ambient/relaxation).
- AAC at 256 kbps as primary; Ogg Vorbis ~192 kbps as fallback for browsers without AAC support.
- Stems are exactly 5 minutes long; the engine handles 30-min playback via the crossfade scheduler per ADR-0010.
- Target file size: < 10 MB per stem after encoding.

### Manifest generation

`tools/assets/build-manifests.mjs` walks `apps/web/public/audio/stems/` and emits one `manifest.json` per soundscape directory, encoding the shape ADR-0010 documented.

### CI guard

`tools/assets/validate-assets.mjs` runs in `ci.yml`:

- Every soundscape ID referenced in `packages/@njz-os/audio-engine/src/soundscape.ts` registry exists in `apps/web/public/audio/stems/`.
- Every spritesheet referenced in `@njz-os/polyworld` scene definitions exists.
- No orphan files in `public/sprites/` or `public/audio/stems/` (catch stale assets that grow the bundle).
- File-size budgets: sprites < 500 KB, stems < 10 MB, total `public/audio/` < 200 MB.

### Phase 1 hosting: `apps/web/public/`

All baseline Phase-1 assets ship inside the webapp's `public/` directory. Vercel serves them as static; cache-control set via `apps/web/vite.config.ts`. Bundle size budget for Phase 1:

- Total `public/audio/`: ≤ 200 MB (10 stems × ~10 MB).
- Total `public/sprites/`: ≤ 5 MB.

### Phase 2 hosting: Cloudflare R2 + asset catalog

When the soundscape library grows past Phase 1's 5 tracks toward the PRD's 40, migrate to **Cloudflare R2**:

- Buckets: `njz-rat-os-audio`, `njz-rat-os-sprites`.
- R2 has zero egress fees and a generous free tier — fits the $0-budget posture.
- An "asset catalog" endpoint added to `services/rat-os-api` (BFF) returns signed URLs + manifest data.
- `@njz-os/audio-engine` and `@njz-os/polyworld` accept either a `public/`-relative URL (Phase 1) or a fully-qualified CDN URL (Phase 2); change is data-only.

Migration ADR (TBD ADR-0019 or later) authored when Phase 2 starts.

### What's NOT in this pipeline

- AI-generated assets — Phase 4 evaluation only; out of scope for Phase 1.
- 3D models — PolyCo.World is Canvas 2D (ADR-0005); no 3D in Phase 1.
- Video — RAT-OS doesn't ship video content in Phase 1.
- Localised text assets — Phase 5 (i18n).

## Consequences

**Positive:**

- Reproducible builds: any contributor can regenerate `public/` artefacts from `assets/sources/` with one `pnpm` command.
- Single shared palette enforces visual coherence in PolyCo.World, addressing the PS-007 risk on "visual coherence vs scope creep."
- Loudness normalisation prevents harsh volume jumps between soundscapes.
- CI guard makes orphan-asset bloat impossible.
- Phase 2 migration path is clear; client API stable across hosts.

**Negative:**

- Aseprite is paid software ($20). Mitigation: LibreSprite (FOSS fork) is acceptable for contributors; we don't gate on the paid license. Acknowledge it in `CONTRIBUTING.md`.
- Source files in `assets/sources/` will eventually outgrow plain Git; Git LFS configuration is a follow-up (cheap to add when needed).
- `public/audio/` at 100+ MB pushes Vercel build time; mitigated by Phase 2 R2 migration.
- FFmpeg `loudnorm` is two-pass for true accuracy; we use one-pass for simplicity (acceptable for ambient content; not for music distribution).

**Neutral:**

- The pipeline is fully scriptable from a CI runner. No manual desktop-tool steps in the deploy path.
- Designer agents can produce assets without touching code; only the `validate-assets` script gates the artefact set.

## Alternatives Considered

- **Vendor pre-built assets from a marketplace** (itch.io tilesets, Freesound CC-BY ambient). Considered as supplements; the *pipeline itself* still needs to be defined for any custom assets we author. Hybrid: use marketplace assets where licensing allows, run them through the same pipeline.
- **Skip the pipeline; hand-place WAVs and PNGs in `public/`.** Rejected: no normalisation guarantees, no validation, no reproducibility, no palette enforcement.
- **Build-time asset processing with Vite plugins** (e.g. `vite-imagetools`). Rejected for source-of-truth role: we want artefact stability across builds and CI hosts; pre-baked artefacts in Git are easier to debug than build-time transforms.
- **Use S3 + CloudFront for Phase 1.** Rejected: cost, egress fees, infra setup. R2 will be the long-term home but Phase 1's small surface fits inside `apps/web/public/`.
- **AI-generated pixel art via Stable Diffusion / similar.** Rejected for Phase 1: quality inconsistent, licensing of training data fraught, pixel-art-style generation still produces non-grid output requiring manual cleanup.

## Related

- ADR-0005 — PolyCo.World renderer (consumes spritesheets via `@njz-os/pixel-art`).
- ADR-0006 — Audio engine base (consumes stems via `AudioBuffer` decode).
- ADR-0010 — Audio engine v0 detail (the manifest shape this pipeline emits).
- `docs/prototype-systems/PS-002-soundscapes.md`, `PS-007-polyco-world.md`.
- `packages/@njz-os/pixel-art/README.md` — receives spritesheet loader.
- `packages/@njz-os/audio-engine/README.md` — consumes built stems.
- `apps/web/public/` — Phase-1 host.
- Cloudflare R2 docs — Phase-2 migration target.

---

> When proposing, leave Status: Proposed. On approval, change to Accepted in a follow-up commit.
> Append a one-line entry to `.agents/DECISION_LOG.md` referencing this ADR.
