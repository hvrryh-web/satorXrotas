# @njz-os/desktop-widget

Tauri-based desktop widget (macOS + Windows). Always-on-top focus timer + soundscape playback controls + PolyCo.World mini-view.

**Status:** Skeleton only. Phase 2+ ships the implementation.

## Why Tauri (planned)

- Small binary footprint (vs Electron).
- Native OS integration for notifications + do-not-disturb.
- WebView frontend shares code with `apps/web` (the Tauri shell is thin).

## Phase 2 Scope

- Quick-start focus timer
- Soundscape play/pause/skip
- Mini PolyCo.World snapshot (latest scene)
- Streak indicator
- OS-level notification routing

Out of scope: full module surface. Users open the webapp for anything beyond glance-and-go.

## ADR

ADR-0013 (Tauri vs Electron) will be opened before Phase 2 work begins.
