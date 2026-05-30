/**
 * PRX-25-PATCH-05 — Toast provider + hook.
 *
 * Wires the pure reducer (toastState.ts) to React + the defaultEventBus.
 * Mounted once at app root:
 *
 *   <ToastProvider>
 *     <App />
 *   </ToastProvider>
 *
 * Children use `useToast()` to call `notify(message, opts)`. The
 * provider also forwards every show/dismiss to defaultEventBus so
 * analytics and other lanes can observe.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  type ReactNode,
} from 'react';
import { defaultEventBus } from '@njz-os/core';
import {
  defaultDismissAfterMs,
  initialToastState,
  toastReducer,
  type ToastVariant,
  type Toast,
} from './toastState';

export interface NotifyOptions {
  variant?: ToastVariant;
  dismissAfterMs?: number | null;
  id?: string;
}

export interface ToastApi {
  notify: (message: string, opts?: NotifyOptions) => string;
  dismiss: (id: string) => void;
  clearAll: () => void;
  visible: Toast[];
  history: Toast[];
}

const ToastContext = createContext<ToastApi | null>(null);

let counter = 0;
function nextId(): string {
  counter += 1;
  return `t-${Date.now()}-${counter}`;
}

export function ToastProvider({
  children,
  maxVisible = 3,
  maxHistory = 25,
}: {
  children: ReactNode;
  maxVisible?: number;
  maxHistory?: number;
}): ReactNode {
  const [state, dispatch] = useReducer(
    toastReducer,
    { maxVisible, maxHistory },
    initialToastState
  );
  const timers = useRef(new Map<string, ReturnType<typeof setTimeout>>());

  const dismiss = useCallback((id: string) => {
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
    dispatch({ kind: 'dismiss', id });
    defaultEventBus.emit('toast.dismiss', { id });
  }, []);

  const notify = useCallback(
    (message: string, opts?: NotifyOptions): string => {
      const variant = opts?.variant ?? 'info';
      const id = opts?.id ?? nextId();
      const dismissAfterMs =
        opts?.dismissAfterMs === undefined
          ? defaultDismissAfterMs[variant]
          : opts.dismissAfterMs;
      const toast: Toast = {
        id,
        variant,
        message,
        createdAt: Date.now(),
        dismissAfterMs,
      };
      dispatch({ kind: 'show', toast });
      defaultEventBus.emit('toast.show', { id, variant, message });
      if (dismissAfterMs !== null && dismissAfterMs > 0) {
        const timer = setTimeout(() => dismiss(id), dismissAfterMs);
        timers.current.set(id, timer);
      }
      return id;
    },
    [dismiss]
  );

  const clearAll = useCallback(() => {
    for (const timer of timers.current.values()) clearTimeout(timer);
    timers.current.clear();
    dispatch({ kind: 'clear-all' });
  }, []);

  useEffect(() => {
    const t = timers.current;
    return () => {
      for (const timer of t.values()) clearTimeout(timer);
      t.clear();
    };
  }, []);

  const api = useMemo<ToastApi>(
    () => ({ notify, dismiss, clearAll, visible: state.visible, history: state.history }),
    [notify, dismiss, clearAll, state.visible, state.history]
  );

  return (
    <ToastContext.Provider value={api}>
      {children}
      <ToastStack toasts={state.visible} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error(
      'useToast() must be called inside <ToastProvider>. ' +
        'Mount it once at the app root.'
    );
  }
  return ctx;
}

function ToastStack({
  toasts,
  onDismiss,
}: {
  toasts: Toast[];
  onDismiss: (id: string) => void;
}): ReactNode {
  if (toasts.length === 0) return null;
  return (
    <div className="njz-toast-stack" aria-label="Notifications">
      {toasts.map((t) => (
        <div
          key={t.id}
          role={t.variant === 'error' ? 'alert' : 'status'}
          aria-live={t.variant === 'error' ? 'assertive' : 'polite'}
          className={`njz-toast njz-toast--${t.variant}`}
        >
          <span className="njz-toast__message">{t.message}</span>
          <button
            type="button"
            onClick={() => onDismiss(t.id)}
            aria-label={`Dismiss ${t.variant} notification`}
            className="njz-toast__dismiss"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
