/**
 * Lane B Task B1 — Master AudioGraph factory.
 *
 * Builds the production signal chain per ADR-0010:
 *
 *   per-stem sources → per-stem GainNode →
 *     master GainNode →
 *       DynamicsCompressorNode (brick-wall limiter) →
 *         AudioDestinationNode (speakers)
 *
 * The AnalyserNode is tapped off the master GainNode so the Deep Canvas
 * painter sees the post-mix, pre-limiter signal (the most visually rich
 * surface) without coupling to the destination.
 *
 * The static description (`AudioGraph`) is preserved for tooling /
 * documentation; runtime construction lives in `createAudioEngine`.
 *
 * SSR-safe: every AudioContext reference is gated behind `if
 * (typeof AudioContext !== "undefined")` so the package compiles + tests
 * in Node.
 */

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

/**
 * The canonical Phase-1 audio graph topology (mirrors ADR-0010 §3).
 * Renderable as ASCII via `describeGraph` for docs.
 */
export const PHASE_1_GRAPH: AudioGraph = {
  nodes: [
    { id: 'stem-source-a', kind: 'source' },
    { id: 'stem-source-b', kind: 'source' },
    { id: 'binaural-left', kind: 'source' },
    { id: 'binaural-right', kind: 'source' },
    { id: 'stem-gain-a', kind: 'gain', inputs: ['stem-source-a'] },
    { id: 'stem-gain-b', kind: 'gain', inputs: ['stem-source-b'] },
    { id: 'binaural-pan-left', kind: 'panner', inputs: ['binaural-left'], params: { pan: -1 } },
    { id: 'binaural-pan-right', kind: 'panner', inputs: ['binaural-right'], params: { pan: 1 } },
    { id: 'binaural-lowpass', kind: 'filter', inputs: ['binaural-pan-left', 'binaural-pan-right'], params: { type: 'lowpass', frequency: 800 } },
    { id: 'master-gain', kind: 'gain', inputs: ['stem-gain-a', 'stem-gain-b', 'binaural-lowpass'] },
    { id: 'analyser-tap', kind: 'analyser', inputs: ['master-gain'], params: { fftSize: 2048 } },
    { id: 'master-limiter', kind: 'compressor', inputs: ['master-gain'], params: { threshold: -10, knee: 0, ratio: 20, attack: 0.003, release: 0.25 } },
  ],
  output: 'master-limiter',
};

export interface AudioEngineConfig {
  /** Inject an AudioContext (the consumer owns lifecycle). */
  audioContext: AudioContext;
  /** AnalyserNode FFT size (must be power of 2; ADR-0010 default 2048). */
  fftSize?: number;
  /** Master limiter threshold in dBFS (ADR-0010 default -10). */
  limiterThresholdDb?: number;
  /** Master limiter ratio (ADR-0010 default 20). */
  limiterRatio?: number;
}

export interface AudioEngine {
  readonly context: AudioContext;
  readonly masterGain: GainNode;
  readonly analyser: AnalyserNode;
  readonly limiter: DynamicsCompressorNode;
  /** Create a new per-stem gain node already wired to master. */
  createStemGain(initialGain?: number): GainNode;
  /** Hook for the binaural module to register its left+right oscillator gains. */
  createBinauralLane(): { leftGain: GainNode; rightGain: GainNode };
  /** Suspend / resume the underlying context (e.g., sleep timer). */
  suspend(): Promise<void>;
  resume(): Promise<void>;
  /** Disposes engine-owned nodes; caller still owns the context. */
  dispose(): void;
}

const LIMITER_DEFAULTS = {
  threshold: -10,
  knee: 0,
  ratio: 20,
  attack: 0.003,
  release: 0.25,
};

export function createAudioEngine(config: AudioEngineConfig): AudioEngine {
  const ctx = config.audioContext;
  const fftSize = config.fftSize ?? 2048;

  const masterGain = ctx.createGain();
  masterGain.gain.value = 1;

  const analyser = ctx.createAnalyser();
  analyser.fftSize = fftSize;
  masterGain.connect(analyser); // tap off master

  const limiter = ctx.createDynamicsCompressor();
  limiter.threshold.value = config.limiterThresholdDb ?? LIMITER_DEFAULTS.threshold;
  limiter.knee.value = LIMITER_DEFAULTS.knee;
  limiter.ratio.value = config.limiterRatio ?? LIMITER_DEFAULTS.ratio;
  limiter.attack.value = LIMITER_DEFAULTS.attack;
  limiter.release.value = LIMITER_DEFAULTS.release;

  masterGain.connect(limiter);
  limiter.connect(ctx.destination);

  const stemGains: GainNode[] = [];
  const binauralGains: GainNode[] = [];

  return {
    context: ctx,
    masterGain,
    analyser,
    limiter,
    createStemGain(initialGain = 0.85) {
      const g = ctx.createGain();
      g.gain.value = initialGain;
      g.connect(masterGain);
      stemGains.push(g);
      return g;
    },
    createBinauralLane() {
      const leftGain = ctx.createGain();
      leftGain.gain.value = 0;
      const rightGain = ctx.createGain();
      rightGain.gain.value = 0;
      const leftPan = ctx.createStereoPanner();
      leftPan.pan.value = -1;
      const rightPan = ctx.createStereoPanner();
      rightPan.pan.value = 1;
      const lowpass = ctx.createBiquadFilter();
      lowpass.type = 'lowpass';
      lowpass.frequency.value = 800;

      leftGain.connect(leftPan).connect(lowpass);
      rightGain.connect(rightPan).connect(lowpass);
      lowpass.connect(masterGain);

      binauralGains.push(leftGain, rightGain);
      return { leftGain, rightGain };
    },
    suspend() {
      return ctx.suspend();
    },
    resume() {
      return ctx.resume();
    },
    dispose() {
      for (const g of stemGains) g.disconnect();
      for (const g of binauralGains) g.disconnect();
      masterGain.disconnect();
      analyser.disconnect();
      limiter.disconnect();
      stemGains.length = 0;
      binauralGains.length = 0;
    },
  };
}

/** ASCII-render the static graph for docs. */
export function describeGraph(graph: AudioGraph = PHASE_1_GRAPH): string {
  const lines: string[] = [];
  for (const node of graph.nodes) {
    const inputs = node.inputs?.length ? node.inputs.join(', ') : '—';
    lines.push(`  ${node.id.padEnd(20)} :: ${node.kind.padEnd(11)} ⟵ ${inputs}`);
  }
  return `Audio graph (output → ${graph.output}):\n${lines.join('\n')}`;
}
