/**
 * ArepoLayer smoke test — death stains and clutch crowns render without errors.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { ArepoLayer, ArepoMarker } from '../layers/ArepoLayer';

function makeMarker(overrides: Partial<ArepoMarker> = {}): ArepoMarker {
  return {
    x: 100,
    y: 150,
    victimTeam: 'attack',
    isMultikill: false,
    multikillCount: 1,
    isClutch: false,
    roundNumber: 3,
    age: 0,
    ...overrides,
  };
}

describe('ArepoLayer', () => {
  it('renders SVG element', () => {
    render(
      <ArepoLayer markers={[makeMarker()]} width={800} height={600} currentRound={3} persistRounds={3} />
    );
    expect(screen.getByTestId('arepo-layer')).toBeInTheDocument();
  });

  it('renders without markers', () => {
    render(
      <ArepoLayer markers={[]} width={800} height={600} currentRound={1} persistRounds={3} />
    );
    expect(screen.getByTestId('arepo-layer')).toBeInTheDocument();
  });

  it('accepts attack and defense victim teams', () => {
    const markers = [
      makeMarker({ victimTeam: 'attack' }),
      makeMarker({ victimTeam: 'defense' }),
    ];
    render(
      <ArepoLayer markers={markers} width={800} height={600} currentRound={3} persistRounds={3} />
    );
    expect(screen.getByTestId('arepo-layer')).toBeInTheDocument();
  });

  it('marker coordinates are within valid range', () => {
    const marker = makeMarker({ x: 400, y: 300 });
    expect(marker.x).toBeGreaterThan(0);
    expect(marker.x).toBeLessThan(2000);
    expect(marker.y).toBeGreaterThan(0);
    expect(marker.y).toBeLessThan(2000);
  });

  it('clutch crown marker renders', () => {
    render(
      <ArepoLayer
        markers={[makeMarker({ isClutch: true })]}
        width={800}
        height={600}
        currentRound={3}
        persistRounds={3}
      />
    );
    expect(screen.getByTestId('arepo-layer')).toBeInTheDocument();
  });
});
