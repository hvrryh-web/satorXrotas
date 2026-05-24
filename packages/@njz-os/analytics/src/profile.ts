export type CognitiveDomain = 'memory' | 'attention' | 'speed' | 'flexibility' | 'spatial';

export type CognitiveProfile = Record<CognitiveDomain, number>;

export type Percentile = number;

export function emptyProfile(): CognitiveProfile {
  return { memory: 0, attention: 0, speed: 0, flexibility: 0, spatial: 0 };
}

export function weakestDomain(profile: CognitiveProfile): CognitiveDomain {
  const entries = Object.entries(profile) as [CognitiveDomain, number][];
  return entries.reduce((min, cur) => (cur[1] < min[1] ? cur : min))[0];
}
