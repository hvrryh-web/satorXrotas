/**
 * SATOR Layer — Layer 1: Golden halo system
 * Renders golden halos for planters, MVPs, and hotstreak players.
 * D3.js SVG rendering.
 */
import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

export interface SatorEvent {
  playerId: string;
  mapX: number;
  mapY: number;
  eventType: 'plant' | 'mvp' | 'hotstreak' | 'ace';
  intensity: number; // 0.0 to 1.0
}

interface SatorLayerProps {
  events: SatorEvent[];
  width: number;
  height: number;
  mapToScreen: (x: number, y: number) => [number, number];
}

const EVENT_COLORS: Record<string, string> = {
  plant: '#FFD700',
  mvp: '#FFA500',
  hotstreak: '#FF6B35',
  ace: '#FF0000',
};

const BASE_RADIUS = 20;

export const SatorLayer: React.FC<SatorLayerProps> = ({
  events,
  width,
  height,
  mapToScreen,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('.sator-halo').remove();

    const halos = svg
      .selectAll<SVGCircleElement, SatorEvent>('.sator-halo')
      .data(events)
      .enter()
      .append('circle')
      .attr('class', 'sator-halo')
      .attr('cx', (d) => mapToScreen(d.mapX, d.mapY)[0])
      .attr('cy', (d) => mapToScreen(d.mapX, d.mapY)[1])
      .attr('r', (d) => BASE_RADIUS * (0.5 + d.intensity * 0.5))
      .attr('fill', 'none')
      .attr('stroke', (d) => EVENT_COLORS[d.eventType] ?? '#FFD700')
      .attr('stroke-width', (d) => 2 + d.intensity * 3)
      .attr('opacity', 0.8);

    // Pulse animation
    halos
      .append('animate')
      .attr('attributeName', 'r')
      .attr('values', (d) => {
        const r = BASE_RADIUS * (0.5 + d.intensity * 0.5);
        return `${r};${r * 1.4};${r}`;
      })
      .attr('dur', '2s')
      .attr('repeatCount', 'indefinite');
  }, [events, mapToScreen]);

  return (
    <svg
      ref={svgRef}
      width={width}
      height={height}
      style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
      data-testid="sator-layer"
    />
  );
};

export default SatorLayer;
