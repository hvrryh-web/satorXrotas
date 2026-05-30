/**
 * Token surface — PRX-25-ENH-05.
 *
 * The single source of truth is `packages/@njz-os/ui/tokens/tokens.json`.
 * Run `node tools/tokens-build/index.mjs` to regenerate `generated.css`
 * and `generated.ts`; CI verifies the generated files are in sync with
 * the JSON SOT via `tools/tokens-build/index.mjs --check`.
 *
 * Backward-compat re-exports `colors`, `space`, `radius`, `typography`
 * preserve the nested shape consumers expect; new code can import
 * `color`/`space`/`radius`/`typography`/`motion` directly from
 * `./generated` for the flat shape.
 */

export { color, space, radius, motion } from './generated';
export type { ColorToken, SpaceToken, RadiusToken, MotionToken } from './generated';

import { color, typography as _typography } from './generated';

export const colors = {
  bg: color.bg,
  bgElevated: color.bgElevated,
  text: color.text,
  textMuted: color.textMuted,
  accent: {
    teal: color.accentTeal,
    warm: color.accentWarm,
    success: color.success,
    danger: color.danger,
  },
  module: {
    focus: color.moduleFocus,
    sound: color.moduleSound,
    blocker: color.moduleBlocker,
    write: color.moduleWrite,
    learn: color.moduleLearn,
    train: color.moduleTrain,
    world: color.moduleWorld,
  },
} as const;

export const typography = {
  display: _typography.familyDisplay,
  body: _typography.familyBody,
  mono: _typography.familyMono,
  scale: {
    xs: _typography.scaleXs,
    sm: _typography.scaleSm,
    base: _typography.scaleBase,
    lg: _typography.scaleLg,
    xl: _typography.scaleXl,
    '2xl': _typography.scale2xl,
    '3xl': _typography.scale3xl,
    '4xl': _typography.scale4xl,
    '5xl': _typography.scale5xl,
  },
  weight: {
    regular: Number(_typography.weightRegular),
    medium: Number(_typography.weightMedium),
    semibold: Number(_typography.weightSemibold),
    bold: Number(_typography.weightBold),
  },
} as const;
