export interface AudioGraphNode {
  id: string;
  kind: 'source' | 'gain' | 'panner' | 'filter' | 'analyser' | 'compressor';
  params?: Record<string, number | string>;
  inputs?: string[];
}

export interface AudioGraph {
  nodes: AudioGraphNode[];
  output: string;
}
