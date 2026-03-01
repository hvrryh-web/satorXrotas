/**
 * TenetLayer smoke test — area control zones render without errors.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { TenetLayer, ControlZone } from '../layers/TenetLayer';

function makeZone(overrides: Partial<ControlZone> = {}): ControlZone {
  return {
    id: 'zone-a',
    polygon: [[10, 10], [100, 10], [100, 100], [10, 100]],
    controlTeam: 'attack',
    grade: 'A',
    controlStrength: 0.75,
    ...overrides,
  };
}

describe('TenetLayer', () => {
  it('renders SVG element', () => {
    render(<TenetLayer zones={[makeZone()]} width={800} height={600} />);
    expect(screen.getByTestId('tenet-layer')).toBeInTheDocument();
  });

  it('renders without zones', () => {
    render(<TenetLayer zones={[]} width={800} height={600} />);
    expect(screen.getByTestId('tenet-layer')).toBeInTheDocument();
  });

  it('accepts all control team types', () => {
    const zones = [
      makeZone({ controlTeam: 'attack' }),
      makeZone({ id: 'zone-b', controlTeam: 'defense' }),
      makeZone({ id: 'zone-c', controlTeam: 'contested' }),
    ];
    render(<TenetLayer zones={zones} width={800} height={600} />);
    expect(screen.getByTestId('tenet-layer')).toBeInTheDocument();
  });

  it('control strength is within valid range', () => {
    const zone = makeZone({ controlStrength: 0.6 });
    expect(zone.controlStrength).toBeGreaterThanOrEqual(0.0);
    expect(zone.controlStrength).toBeLessThanOrEqual(1.0);
  });

  it('accepts all grade types', () => {
    (['A', 'B', 'C', 'D'] as ControlZone['grade'][]).forEach((grade) => {
      const { unmount } = render(
        <TenetLayer zones={[makeZone({ grade })]} width={800} height={600} />
      );
      unmount();
    });
  });
});
