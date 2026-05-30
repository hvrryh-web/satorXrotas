import { describe, expect, it, vi } from 'vitest';
import { createEventBus, type NjzEventMap } from './events';

describe('createEventBus', () => {
  it('delivers a payload to a single subscriber', () => {
    const bus = createEventBus<NjzEventMap>();
    const seen: string[] = [];
    bus.on('toast.show', (p) => seen.push(p.message));
    bus.emit('toast.show', { id: 't1', variant: 'info', message: 'hello' });
    expect(seen).toEqual(['hello']);
  });

  it('delivers to multiple subscribers in subscription order', () => {
    const bus = createEventBus<NjzEventMap>();
    const order: number[] = [];
    bus.on('toast.show', () => order.push(1));
    bus.on('toast.show', () => order.push(2));
    bus.on('toast.show', () => order.push(3));
    bus.emit('toast.show', { id: 't', variant: 'info', message: 'm' });
    expect(order).toEqual([1, 2, 3]);
  });

  it('returns an unsubscribe function from on() that removes only that listener', () => {
    const bus = createEventBus<NjzEventMap>();
    const a = vi.fn();
    const b = vi.fn();
    const unsubA = bus.on('toast.dismiss', a);
    bus.on('toast.dismiss', b);
    unsubA();
    bus.emit('toast.dismiss', { id: 'x' });
    expect(a).not.toHaveBeenCalled();
    expect(b).toHaveBeenCalledOnce();
  });

  it('off() removes a specific listener by reference', () => {
    const bus = createEventBus<NjzEventMap>();
    const a = vi.fn();
    bus.on('toast.dismiss', a);
    bus.off('toast.dismiss', a);
    bus.emit('toast.dismiss', { id: 'y' });
    expect(a).not.toHaveBeenCalled();
  });

  it('isolates listener errors via setErrorHandler', () => {
    const bus = createEventBus<NjzEventMap>();
    const errorHandler = vi.fn();
    bus.setErrorHandler(errorHandler);
    const survivor = vi.fn();
    bus.on('toast.show', () => {
      throw new Error('boom');
    });
    bus.on('toast.show', survivor);
    bus.emit('toast.show', { id: 'z', variant: 'error', message: 'err' });
    expect(survivor).toHaveBeenCalledOnce();
    expect(errorHandler).toHaveBeenCalledOnce();
    expect((errorHandler.mock.calls[0]?.[0] as Error).message).toBe('boom');
  });

  it('clear() with an event name removes only that event', () => {
    const bus = createEventBus<NjzEventMap>();
    const a = vi.fn();
    const b = vi.fn();
    bus.on('toast.show', a);
    bus.on('toast.dismiss', b);
    bus.clear('toast.show');
    bus.emit('toast.show', { id: 'q', variant: 'info', message: 'q' });
    bus.emit('toast.dismiss', { id: 'q' });
    expect(a).not.toHaveBeenCalled();
    expect(b).toHaveBeenCalledOnce();
  });

  it('clear() with no argument removes all listeners', () => {
    const bus = createEventBus<NjzEventMap>();
    const a = vi.fn();
    const b = vi.fn();
    bus.on('toast.show', a);
    bus.on('toast.dismiss', b);
    bus.clear();
    bus.emit('toast.show', { id: 'q', variant: 'info', message: 'q' });
    bus.emit('toast.dismiss', { id: 'q' });
    expect(a).not.toHaveBeenCalled();
    expect(b).not.toHaveBeenCalled();
  });

  it('listenerCount() reports the number of active listeners', () => {
    const bus = createEventBus<NjzEventMap>();
    expect(bus.listenerCount('toast.show')).toBe(0);
    const unsubA = bus.on('toast.show', () => {});
    bus.on('toast.show', () => {});
    expect(bus.listenerCount('toast.show')).toBe(2);
    unsubA();
    expect(bus.listenerCount('toast.show')).toBe(1);
  });

  it('emit() on an event with no listeners is a no-op', () => {
    const bus = createEventBus<NjzEventMap>();
    expect(() =>
      bus.emit('toast.show', { id: 'q', variant: 'info', message: 'q' })
    ).not.toThrow();
  });

  it('snapshot semantics: listeners removed during emit still receive the current event', () => {
    const bus = createEventBus<NjzEventMap>();
    const a = vi.fn();
    const b = vi.fn();
    const unsubA = bus.on('toast.show', () => {
      a();
      unsubA();
    });
    bus.on('toast.show', b);
    bus.emit('toast.show', { id: '1', variant: 'info', message: '1' });
    bus.emit('toast.show', { id: '2', variant: 'info', message: '2' });
    expect(a).toHaveBeenCalledOnce();
    expect(b).toHaveBeenCalledTimes(2);
  });
});
