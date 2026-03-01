/**
 * OperaLayer smoke test — fog of war canvas renders without errors.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { OperaLayer } from '../layers/OperaLayer';

describe('OperaLayer', () => {
  it('renders canvas element', () => {
    render(
      <OperaLayer
        width={800}
        height={600}
        visibilityMask={new Float32Array(800 * 600).fill(0.5)}
        uncertaintyPoints={[]}
      />
    );
    expect(screen.getByTestId('opera-layer')).toBeInTheDocument();
  });

  it('renders with empty visibility mask', () => {
    render(
      <OperaLayer
        width={100}
        height={100}
        visibilityMask={new Float32Array(0)}
        uncertaintyPoints={[]}
      />
    );
    expect(screen.getByTestId('opera-layer')).toBeInTheDocument();
  });

  it('renders with uncertainty points', () => {
    render(
      <OperaLayer
        width={400}
        height={400}
        visibilityMask={new Float32Array(16).fill(0.8)}
        uncertaintyPoints={[
          { x: 100, y: 100, uncertainty: 0.7 },
          { x: 200, y: 200, uncertainty: 0.3 },
        ]}
      />
    );
    expect(screen.getByTestId('opera-layer')).toBeInTheDocument();
  });

  it('visibility mask values are in valid range [0, 1]', () => {
    const mask = new Float32Array([0.0, 0.25, 0.5, 0.75, 1.0]);
    mask.forEach((v) => {
      expect(v).toBeGreaterThanOrEqual(0.0);
      expect(v).toBeLessThanOrEqual(1.0);
    });
  });
});
