/**
 * useSpatialData — Hook for fetching and transforming spatial event data
 * for all five SATOR Square layers.
 */
import { useState, useEffect, useCallback } from 'react';

export interface SpatialDataState {
  satorEvents: SatorEventData[];
  arepoMarkers: ArepoMarkerData[];
  rotasTrails: RotasTrailData[];
  controlZones: ControlZoneData[];
  visibilityMask: Float32Array | null;
  loading: boolean;
  error: Error | null;
}

export interface SatorEventData {
  playerId: string;
  mapX: number;
  mapY: number;
  eventType: 'plant' | 'mvp' | 'hotstreak' | 'ace';
  intensity: number;
}

export interface ArepoMarkerData {
  x: number;
  y: number;
  victimTeam: 'attack' | 'defense';
  isMultikill: boolean;
  multikillCount: number;
  isClutch: boolean;
  roundNumber: number;
  age: number;
}

export interface RotasTrailData {
  playerId: string;
  team: 'attack' | 'defense';
  positions: Array<{ x: number; y: number; tick: number }>;
  directionLR: -1 | 0 | 1;
}

export interface ControlZoneData {
  id: string;
  polygon: Array<[number, number]>;
  controlTeam: 'attack' | 'defense' | 'contested';
  grade: 'A' | 'B' | 'C' | 'D';
  controlStrength: number;
}

const EMPTY_MASK = new Float32Array(0);

export function useSpatialData(matchId: string, roundNumber: number): SpatialDataState {
  const [state, setState] = useState<SpatialDataState>({
    satorEvents: [],
    arepoMarkers: [],
    rotasTrails: [],
    controlZones: [],
    visibilityMask: null,
    loading: false,
    error: null,
  });

  const fetchData = useCallback(async () => {
    if (!matchId) return;
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const [satorRes, arepoRes, rotasRes] = await Promise.all([
        fetch(`/api/matches/${matchId}/rounds/${roundNumber}/sator-events`),
        fetch(`/api/matches/${matchId}/rounds/${roundNumber}/arepo-markers`),
        fetch(`/api/matches/${matchId}/rounds/${roundNumber}/rotas-trails`),
      ]);

      const [satorEvents, arepoMarkers, rotasTrails] = await Promise.all([
        satorRes.json(),
        arepoRes.json(),
        rotasRes.json(),
      ]);

      setState({
        satorEvents,
        arepoMarkers,
        rotasTrails,
        controlZones: [],
        visibilityMask: EMPTY_MASK,
        loading: false,
        error: null,
      });
    } catch (err) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err : new Error(String(err)),
      }));
    }
  }, [matchId, roundNumber]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return state;
}
