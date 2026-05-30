/**
 * PRX-25-PATCH-05 — Pure state engine for the toast surface.
 *
 * Separated from the React provider so the state transitions can be
 * unit-tested without a renderer. The provider (ToastProvider.tsx) wires
 * this reducer to React + the defaultEventBus.
 */

export type ToastVariant = 'info' | 'success' | 'warning' | 'error';

export interface Toast {
  id: string;
  variant: ToastVariant;
  message: string;
  createdAt: number;
  dismissAfterMs: number | null;
}

export interface ToastState {
  visible: Toast[];
  history: Toast[];
  maxVisible: number;
  maxHistory: number;
}

export type ToastAction =
  | { kind: 'show'; toast: Toast }
  | { kind: 'dismiss'; id: string }
  | { kind: 'clear-all' };

export function initialToastState(opts?: {
  maxVisible?: number;
  maxHistory?: number;
}): ToastState {
  return {
    visible: [],
    history: [],
    maxVisible: opts?.maxVisible ?? 3,
    maxHistory: opts?.maxHistory ?? 25,
  };
}

export function toastReducer(state: ToastState, action: ToastAction): ToastState {
  switch (action.kind) {
    case 'show': {
      const candidates = [...state.visible, action.toast];
      if (candidates.length <= state.maxVisible) {
        return { ...state, visible: candidates };
      }
      const overflow = candidates.slice(0, candidates.length - state.maxVisible);
      const visible = candidates.slice(candidates.length - state.maxVisible);
      const history = [...overflow.reverse(), ...state.history].slice(
        0,
        state.maxHistory
      );
      return { ...state, visible, history };
    }
    case 'dismiss': {
      const target = state.visible.find((t) => t.id === action.id);
      if (!target) return state;
      const visible = state.visible.filter((t) => t.id !== action.id);
      const history = [target, ...state.history].slice(0, state.maxHistory);
      return { ...state, visible, history };
    }
    case 'clear-all': {
      const history = [...state.visible.slice().reverse(), ...state.history].slice(
        0,
        state.maxHistory
      );
      return { ...state, visible: [], history };
    }
    default:
      return state;
  }
}

/**
 * Default auto-dismiss durations per variant, in ms. Errors stay
 * up longer because users typically need more time to read and act
 * on them; info/success disappear quickly.
 */
export const defaultDismissAfterMs: Record<ToastVariant, number | null> = {
  info: 4_000,
  success: 4_000,
  warning: 6_000,
  error: 8_000,
};
