/**
 * AREPO Layer — Layer 4: Death stains, multikill persistence, clutch crowns.
 * D3.js SVG rendering.
 */
import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

export interface ArepoMarker {
  x: number;
  y: number;
  victimTeam: 'attack' | 'defense';
  isMultikill: boolean;
  multikillCount: number;
  isClutch: boolean;
  roundNumber: number;
  age: number; // Rounds since death — for persistence decay
}

interface ArepoLayerProps {
  markers: ArepoMarker[];
  width: number;
  height: number;
  currentRound: number;
  persistRounds: number; // How many rounds to show stains
}

export const ArepoLayer: React.FC<ArepoLayerProps> = ({
  markers,
  width,
  height,
  currentRound,
  persistRounds = 3,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('.arepo-marker').remove();

    const visible = markers.filter((m) => currentRound - m.roundNumber <= persistRounds);

    // Death stains
    svg
      .selectAll<SVGCircleElement, ArepoMarker>('.arepo-stain')
      .data(visible)
      .enter()
      .append('circle')
      .attr('class', 'arepo-marker arepo-stain')
      .attr('cx', (d) => d.x)
      .attr('cy', (d) => d.y)
      .attr('r', (d) => 4 + (d.multikillCount - 1) * 2)
      .attr('fill', (d) => d.victimTeam === 'attack' ? '#4A90D9' : '#E85D5D')
      .attr('opacity', (d) => Math.max(0.2, 1.0 - (currentRound - d.roundNumber) * 0.25));

    // Clutch crowns
    const clutches = visible.filter((m) => m.isClutch);
    svg
      .selectAll<SVGTextElement, ArepoMarker>('.arepo-crown')
      .data(clutches)
      .enter()
      .append('text')
      .attr('class', 'arepo-marker arepo-crown')
      .attr('x', (d) => d.x)
      .attr('y', (d) => d.y - 10)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .text('♛')
      .attr('fill', '#FFD700');
  }, [markers, currentRound, persistRounds]);

  return (
    <svg
      ref={svgRef}
      width={width}
      height={height}
      style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
      data-testid="arepo-layer"
    />
  );
};

export default ArepoLayer;
