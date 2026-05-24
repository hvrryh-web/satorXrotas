export type FrequencyBand = 'delta' | 'theta' | 'alpha' | 'beta' | 'gamma';

export interface BinauralPreset {
  id: string;
  band: FrequencyBand;
  carrierHz: number;
  beatHz: number;
  durationMs: number;
}

export const bandRange: Record<FrequencyBand, [number, number]> = {
  delta: [1, 4],
  theta: [4, 8],
  alpha: [8, 14],
  beta: [14, 30],
  gamma: [30, 100],
};
