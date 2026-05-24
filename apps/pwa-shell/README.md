# @njz-os/pwa-shell

PWA wrapper configuration for `apps/web` — manifest, service worker, icon set, install prompts.

**Status:** Skeleton only. Phase 2 ships installable PWA targeting Lighthouse PWA score ≥ 90.

## Phase 2 Deliverables

- `manifest.webmanifest` — app metadata, icons, theme color.
- `sw.ts` — service worker for offline shell + asset caching.
- Install prompt UX hook in `apps/web/src/shared/install-prompt`.
- Lighthouse PWA audit baseline + monitoring.

## Why Separate From `apps/web`

The webapp builds the runtime; the PWA shell defines the platform integration. Keeping them separate makes the PWA story easy to reason about and easy to disable for embed cases (e.g., iframe in a help center).
