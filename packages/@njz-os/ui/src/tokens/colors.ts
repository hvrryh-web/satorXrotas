export const colors = {
  bg: '#0F172A',
  bgElevated: '#1E293B',
  text: '#F8FAFC',
  textMuted: '#94A3B8',
  accent: {
    teal: '#14B8A6',
    warm: '#F97316',
    success: '#22C55E',
    danger: '#EF4444',
  },
  module: {
    focus: '#F97316',
    sound: '#A855F7',
    blocker: '#EF4444',
    write: '#0EA5E9',
    learn: '#EAB308',
    train: '#22C55E',
    world: '#14B8A6',
  },
} as const;

export type ColorToken = typeof colors;
