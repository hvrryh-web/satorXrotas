# @njz-os/ui

Design tokens, error boundary, toast surface, and (eventually) component primitives for NJZ RAT-OS.

## Surface

### Tokens (PRX-25-ENH-05)

Single source of truth: `tokens/tokens.json`. Compiled by
`tools/tokens-build/index.mjs` into:

- `src/tokens/generated.css` — CSS custom properties (`--njz-color-bg`, …) for use in CSS / CSS Modules.
- `src/tokens/generated.ts` — flat typed exports (`color.bg`, `space[4]`, `motion.durationFast`).

The `src/tokens/index.ts` barrel re-exports both the flat shape and a
backward-compat nested shape (`colors.accent.teal`, `typography.scale.xs`).

#### Editing protocol

1. Change values in `packages/@njz-os/ui/tokens/tokens.json`.
2. `pnpm tokens:build` — regenerates `generated.css` + `generated.ts`.
3. Commit `tokens.json` + the two generated files together.
4. CI verifies sync via `tools/tokens-build/index.mjs --check`.

### Error boundary (PRX-25-PATCH-03)

`<ErrorBoundary moduleSlug="focus-hero" moduleLabel="Focus Hero">…</ErrorBoundary>`

Friendly fallback + recover CTA. Emits `errorBoundary.caught` on the
`defaultEventBus` from `@njz-os/core`.

### Toast surface (PRX-25-PATCH-05)

Mount once at app root:

```tsx
import { ToastProvider } from '@njz-os/ui';
<ToastProvider maxVisible={3}>…</ToastProvider>
```

Children consume:

```tsx
import { useToast } from '@njz-os/ui';
const { notify, dismiss } = useToast();
notify('Saved', { variant: 'success' });
```

Variants: `info` · `success` · `warning` · `error`. Errors get
`aria-live=assertive`; others polite. Auto-dismiss timings tuned per
variant (errors longer). Emits `toast.show` + `toast.dismiss` on the
default event bus.

## Roadmap

- Phase 1: Button, Panel, Toggle, Checkbox, Card, Modal, Drawer primitives.
- Phase 2: Storybook publication, visual regression baseline.

## Extending Upstream

Once `@njz/ui` (upstream in ZeSporteXte) stabilises, re-export selected primitives here and document any RAT-OS overrides.
