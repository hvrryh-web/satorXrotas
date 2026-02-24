/**
 * ROTAS Layer — Layer 5: Rotation trails, LR balance wheel, motion dust.
 * WebGL (Canvas) rendering for particle system performance.
 */
import React, { useEffect, useRef } from 'react';

export interface RotasTrail {
  playerId: string;
  team: 'attack' | 'defense';
  positions: Array<{ x: number; y: number; tick: number }>;
  directionLR: -1 | 0 | 1; // -1 left flank, 0 mid, 1 right flank
}

interface RotasLayerProps {
  trails: RotasTrail[];
  width: number;
  height: number;
  currentTick: number;
  trailLength: number; // Number of positions to render
}

const TEAM_TRAIL_COLORS = {
  attack: 'rgba(74, 144, 217, 0.6)',
  defense: 'rgba(232, 93, 93, 0.6)',
};

export const RotasLayer: React.FC<RotasLayerProps> = ({
  trails,
  width,
  height,
  currentTick,
  trailLength = 10,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    for (const trail of trails) {
      const recent = trail.positions
        .filter((p) => p.tick <= currentTick && p.tick >= currentTick - trailLength)
        .sort((a, b) => a.tick - b.tick);

      if (recent.length < 2) continue;

      ctx.beginPath();
      ctx.moveTo(recent[0].x, recent[0].y);
      for (let i = 1; i < recent.length; i++) {
        ctx.lineTo(recent[i].x, recent[i].y);
      }
      ctx.strokeStyle = TEAM_TRAIL_COLORS[trail.team];
      ctx.lineWidth = 2;
      ctx.stroke();

      // Dust particle at trail head
      const head = recent[recent.length - 1];
      ctx.beginPath();
      ctx.arc(head.x, head.y, 3, 0, Math.PI * 2);
      ctx.fillStyle = TEAM_TRAIL_COLORS[trail.team].replace('0.6', '1.0');
      ctx.fill();
    }
  }, [trails, currentTick, trailLength, width, height]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
      data-testid="rotas-layer"
    />
  );
};

export default RotasLayer;
