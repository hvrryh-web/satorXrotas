/**
 * RotasLayer smoke test — rotation trails render without errors.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { RotasLayer, RotasTrail } from '../layers/RotasLayer';

function makeTrail(overrides: Partial<RotasTrail> = {}): RotasTrail {
  return {
    playerId: 'player-uuid-1',
    team: 'attack',
    positions: [
      { x: 100, y: 100, tick: 1 },
      { x: 110, y: 105, tick: 2 },
      { x: 120, y: 110, tick: 3 },
    ],
    directionLR: 0,
    ...overrides,
  };
}

describe('RotasLayer', () => {
  it('renders canvas element', () => {
    render(
      <RotasLayer trails={[makeTrail()]} width={800} height={600} currentTick={3} trailLength={10} />
    );
    expect(screen.getByTestId('rotas-layer')).toBeInTheDocument();
  });

  it('renders without trails', () => {
    render(
      <RotasLayer trails={[]} width={800} height={600} currentTick={1} trailLength={10} />
    );
    expect(screen.getByTestId('rotas-layer')).toBeInTheDocument();
  });

  it('accepts attack and defense teams', () => {
    const trails = [
      makeTrail({ team: 'attack' }),
      makeTrail({ playerId: 'player-2', team: 'defense' }),
    ];
    render(
      <RotasLayer trails={trails} width={800} height={600} currentTick={3} trailLength={10} />
    );
    expect(screen.getByTestId('rotas-layer')).toBeInTheDocument();
  });

  it('accepts all directionLR values', () => {
    ([-1, 0, 1] as RotasTrail['directionLR'][]).forEach((dir) => {
      const { unmount } = render(
        <RotasLayer
          trails={[makeTrail({ directionLR: dir })]}
          width={800}
          height={600}
          currentTick={3}
          trailLength={10}
        />
      );
      unmount();
    });
  });

  it('trail positions have valid coordinates', () => {
    const trail = makeTrail();
    trail.positions.forEach((pos) => {
      expect(pos.x).toBeGreaterThanOrEqual(0);
      expect(pos.y).toBeGreaterThanOrEqual(0);
      expect(pos.tick).toBeGreaterThan(0);
    });
  });
});
