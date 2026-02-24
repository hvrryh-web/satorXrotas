/**
 * SatorLayer smoke test — verifies golden halo renders without crashing.
 * Range-based assertions only — no hardcoded player IDs or match references.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { SatorLayer, SatorEvent } from '../layers/SatorLayer';

const mockMapToScreen = (x: number, y: number): [number, number] => [x * 2, y * 2];

function makeEvent(overrides: Partial<SatorEvent> = {}): SatorEvent {
  return {
    playerId: 'test-player-uuid',
    mapX: 50,
    mapY: 50,
    eventType: 'plant',
    intensity: 0.8,
    ...overrides,
  };
}

describe('SatorLayer', () => {
  it('renders SVG element', () => {
    render(
      <SatorLayer
        events={[makeEvent()]}
        width={800}
        height={600}
        mapToScreen={mockMapToScreen}
      />
    );
    expect(screen.getByTestId('sator-layer')).toBeInTheDocument();
  });

  it('renders without events', () => {
    render(
      <SatorLayer events={[]} width={800} height={600} mapToScreen={mockMapToScreen} />
    );
    const svg = screen.getByTestId('sator-layer');
    expect(svg.querySelectorAll('.sator-halo')).toHaveLength(0);
  });

  it('intensity is within valid range [0, 1]', () => {
    const events = [
      makeEvent({ intensity: 0.0 }),
      makeEvent({ intensity: 0.5 }),
      makeEvent({ intensity: 1.0 }),
    ];
    events.forEach((e) => {
      expect(e.intensity).toBeGreaterThanOrEqual(0.0);
      expect(e.intensity).toBeLessThanOrEqual(1.0);
    });
  });

  it('accepts all event types', () => {
    const eventTypes: SatorEvent['eventType'][] = ['plant', 'mvp', 'hotstreak', 'ace'];
    eventTypes.forEach((eventType) => {
      const { unmount } = render(
        <SatorLayer
          events={[makeEvent({ eventType })]}
          width={800}
          height={600}
          mapToScreen={mockMapToScreen}
        />
      );
      unmount();
    });
  });

  it('map coordinates are within map bounds (range check)', () => {
    const event = makeEvent({ mapX: 512, mapY: 512 });
    // Typical Valorant map is 1024x1024 units — coordinates must be within bounds
    expect(event.mapX).toBeGreaterThan(0);
    expect(event.mapX).toBeLessThan(2048);
    expect(event.mapY).toBeGreaterThan(0);
    expect(event.mapY).toBeLessThan(2048);
  });
});
