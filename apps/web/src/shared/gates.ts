/**
 * Phase gate guard. Throws at module load time if the named gate is LOCKED
 * and STRICT_GATES is enabled (env or window flag).
 *
 * Per `.agents/PHASE_GATES.md`: feature modules import this with their gate
 * name. In Phase 0 the throw is dormant so the shell compiles and renders
 * placeholders. Flip STRICT_GATES on (`VITE_STRICT_GATES=true`) in CI to
 * catch accidental Phase-1+ feature work landing while gates are LOCKED.
 */

type GateStatus = 'OPEN' | 'LOCKED';

const gateStatus: Record<string, GateStatus> = {
  'G0.framework': 'OPEN',
  'G0.docs': 'OPEN',
  'G0.skeleton': 'OPEN',
  'G0.adapters': 'OPEN',
  'G1.focus-hero': 'LOCKED',
  'G1.soundscapes': 'LOCKED',
  'G1.blocker': 'LOCKED',
  'G1.polyworld-office': 'LOCKED',
  'G1.vaultbrain-live': 'LOCKED',
  'G2.brain-training': 'LOCKED',
  'G2.writing-space': 'LOCKED',
  'G2.micro-learning': 'LOCKED',
  'G2.polyworld-home': 'LOCKED',
  'G2.mobile-pwa': 'LOCKED',
  'G2.premium': 'LOCKED',
  'G3.social': 'LOCKED',
  'G3.native': 'LOCKED',
  'G3.events': 'LOCKED',
};

const strictGatesEnabled = import.meta.env.VITE_STRICT_GATES === 'true';

export function assertGateOpen(gate: string): void {
  const status = gateStatus[gate];
  if (status === undefined) {
    throw new Error(`Unknown gate: ${gate}`);
  }
  if (status === 'LOCKED' && strictGatesEnabled) {
    throw new Error(
      `Gate ${gate} is LOCKED. See .agents/PHASE_GATES.md for unlock criteria.`,
    );
  }
}

export function isGateOpen(gate: string): boolean {
  const status = gateStatus[gate];
  if (status === undefined) return false;
  return status === 'OPEN';
}
