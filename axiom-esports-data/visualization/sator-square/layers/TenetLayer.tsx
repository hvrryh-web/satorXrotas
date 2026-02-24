/**
 * TENET Layer — Layer 3: Area control grading, mutual exclusion zones.
 * D3.js SVG rendering.
 */
import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

export interface ControlZone {
  id: string;
  polygon: Array<[number, number]>; // Screen coordinates
  controlTeam: 'attack' | 'defense' | 'contested';
  grade: 'A' | 'B' | 'C' | 'D';
  controlStrength: number; // 0.0 to 1.0
}

const CONTROL_COLORS = {
  attack: '#4A90D9',
  defense: '#E85D5D',
  contested: '#F5A623',
};

interface TenetLayerProps {
  zones: ControlZone[];
  width: number;
  height: number;
}

export const TenetLayer: React.FC<TenetLayerProps> = ({ zones, width, height }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('.tenet-zone').remove();

    const line = d3.line<[number, number]>().x((d) => d[0]).y((d) => d[1]);

    svg
      .selectAll<SVGPathElement, ControlZone>('.tenet-zone')
      .data(zones)
      .enter()
      .append('path')
      .attr('class', 'tenet-zone')
      .attr('d', (d) => line(d.polygon) + 'Z')
      .attr('fill', (d) => CONTROL_COLORS[d.controlTeam])
      .attr('fill-opacity', (d) => 0.15 + d.controlStrength * 0.25)
      .attr('stroke', (d) => CONTROL_COLORS[d.controlTeam])
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.6);
  }, [zones]);

  return (
    <svg
      ref={svgRef}
      width={width}
      height={height}
      style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
      data-testid="tenet-layer"
    />
  );
};

export default TenetLayer;
