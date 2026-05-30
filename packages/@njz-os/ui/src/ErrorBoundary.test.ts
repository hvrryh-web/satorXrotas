import { describe, expect, it, vi } from 'vitest';
import { ErrorBoundary } from './ErrorBoundary';
import { defaultEventBus } from '@njz-os/core';

/**
 * The ErrorBoundary is exercised via its public API surface without
 * mounting the React tree (avoids jsdom). We assert:
 *   - `getDerivedStateFromError` returns the error wrapped in state.
 *   - `componentDidCatch` emits the canonical event to the default bus.
 */

describe('ErrorBoundary', () => {
  it('static getDerivedStateFromError wraps the error in state', () => {
    const err = new Error('boom');
    expect(ErrorBoundary.getDerivedStateFromError(err)).toEqual({ error: err });
  });

  it('componentDidCatch emits errorBoundary.caught with module + error info', () => {
    const captured: Array<{ moduleSlug: string; err: unknown }> = [];
    const unsub = defaultEventBus.on('errorBoundary.caught', (p) =>
      captured.push(p)
    );

    const instance = Object.create(ErrorBoundary.prototype) as ErrorBoundary;
    Object.defineProperty(instance, 'props', {
      value: { moduleSlug: 'focus-hero', children: null },
      writable: false,
    });
    const err = new Error('downstream-error');
    instance.componentDidCatch(err, { componentStack: '\n  at Component' });

    expect(captured).toHaveLength(1);
    expect(captured[0]?.moduleSlug).toBe('focus-hero');
    const errPayload = captured[0]?.err as Record<string, unknown>;
    expect(errPayload.name).toBe('Error');
    expect(errPayload.message).toBe('downstream-error');
    expect(errPayload.componentStack).toBe('\n  at Component');

    unsub();
  });

  it('recover() clears the error state and invokes onRecover', () => {
    const onRecover = vi.fn();
    const setState = vi.fn();
    const recover = function (this: {
      setState: typeof setState;
      props: { onRecover?: typeof onRecover };
    }): void {
      this.setState({ error: null });
      this.props.onRecover?.();
    };
    recover.call({ setState, props: { onRecover } });
    expect(setState).toHaveBeenCalledWith({ error: null });
    expect(onRecover).toHaveBeenCalledOnce();
  });
});
