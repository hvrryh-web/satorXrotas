import { describe, expect, it } from 'vitest';
import {
  initialToastState,
  toastReducer,
  defaultDismissAfterMs,
  type Toast,
} from './toastState';

function makeToast(id: string, message = id): Toast {
  return {
    id,
    variant: 'info',
    message,
    createdAt: Date.now(),
    dismissAfterMs: defaultDismissAfterMs.info,
  };
}

describe('toastReducer', () => {
  it('show: appends a toast under maxVisible', () => {
    const s = toastReducer(initialToastState(), { kind: 'show', toast: makeToast('a') });
    expect(s.visible.map((t) => t.id)).toEqual(['a']);
    expect(s.history).toHaveLength(0);
  });

  it('show: overflows oldest into history when at capacity', () => {
    let s = initialToastState({ maxVisible: 2 });
    s = toastReducer(s, { kind: 'show', toast: makeToast('a') });
    s = toastReducer(s, { kind: 'show', toast: makeToast('b') });
    s = toastReducer(s, { kind: 'show', toast: makeToast('c') });
    expect(s.visible.map((t) => t.id)).toEqual(['b', 'c']);
    expect(s.history.map((t) => t.id)).toEqual(['a']);
  });

  it('dismiss: removes the toast and moves it to history (newest-first)', () => {
    let s = initialToastState();
    s = toastReducer(s, { kind: 'show', toast: makeToast('a') });
    s = toastReducer(s, { kind: 'show', toast: makeToast('b') });
    s = toastReducer(s, { kind: 'dismiss', id: 'a' });
    expect(s.visible.map((t) => t.id)).toEqual(['b']);
    expect(s.history.map((t) => t.id)).toEqual(['a']);
  });

  it('dismiss: unknown id is a no-op (preserves identity)', () => {
    const before = toastReducer(initialToastState(), {
      kind: 'show',
      toast: makeToast('a'),
    });
    const after = toastReducer(before, { kind: 'dismiss', id: 'nope' });
    expect(after).toBe(before);
  });

  it('clear-all: drains visible into history (newest-first)', () => {
    let s = initialToastState();
    s = toastReducer(s, { kind: 'show', toast: makeToast('a') });
    s = toastReducer(s, { kind: 'show', toast: makeToast('b') });
    s = toastReducer(s, { kind: 'clear-all' });
    expect(s.visible).toEqual([]);
    expect(s.history.map((t) => t.id)).toEqual(['b', 'a']);
  });

  it('history caps at maxHistory', () => {
    let s = initialToastState({ maxVisible: 1, maxHistory: 2 });
    for (const id of ['a', 'b', 'c', 'd', 'e']) {
      s = toastReducer(s, { kind: 'show', toast: makeToast(id) });
    }
    expect(s.visible.map((t) => t.id)).toEqual(['e']);
    expect(s.history.map((t) => t.id)).toEqual(['d', 'c']);
  });

  it('defaultDismissAfterMs uses longer duration for warnings + errors', () => {
    expect(defaultDismissAfterMs.error).toBeGreaterThan(defaultDismissAfterMs.info!);
    expect(defaultDismissAfterMs.warning).toBeGreaterThan(defaultDismissAfterMs.success!);
  });
});
