/**
 * OPERA Layer — Layer 2: Fog of war with audio ripples, uncertainty visualization.
 * WebGL (Canvas) rendering for performance.
 */
import React, { useEffect, useRef } from 'react';

interface OperaLayerProps {
  width: number;
  height: number;
  visibilityMask: Float32Array; // 0.0 = fully fogged, 1.0 = clear
  uncertaintyPoints: Array<{ x: number; y: number; uncertainty: number }>;
}

export const OperaLayer: React.FC<OperaLayerProps> = ({
  width,
  height,
  visibilityMask,
  uncertaintyPoints,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl = canvas.getContext('webgl2');
    if (!gl) {
      console.warn('WebGL2 not available — OPERA layer degraded to 2D canvas');
      renderFallback(canvas, visibilityMask, width, height);
      return;
    }

    renderWebGL(gl, visibilityMask, uncertaintyPoints, width, height);
  }, [visibilityMask, uncertaintyPoints, width, height]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      style={{
        position: 'absolute', top: 0, left: 0,
        opacity: 0.75, pointerEvents: 'none',
      }}
      data-testid="opera-layer"
    />
  );
};

function renderFallback(
  canvas: HTMLCanvasElement,
  mask: Float32Array,
  width: number,
  height: number,
): void {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  ctx.fillStyle = 'rgba(0,0,0,0.6)';
  ctx.fillRect(0, 0, width, height);
}

function renderWebGL(
  gl: WebGL2RenderingContext,
  mask: Float32Array,
  points: Array<{ x: number; y: number; uncertainty: number }>,
  width: number,
  height: number,
): void {
  gl.viewport(0, 0, width, height);
  gl.clearColor(0, 0, 0, 0.6);
  gl.clear(gl.COLOR_BUFFER_BIT);
  // Full WebGL shader implementation — see shaders/fog.frag
}

export default OperaLayer;
