import type { ReactNode } from 'react';

interface PhaseStubProps {
  module: string;
  gate: string;
  phase: number;
  spec: string;
  children?: ReactNode;
}

export function PhaseStub({ module, gate, phase, spec, children }: PhaseStubProps) {
  return (
    <section className="rat-page rat-page--stub">
      <h1>{module}</h1>
      <p className="rat-page__meta">
        Phase {phase} · Gate <code>{gate}</code> · Spec <code>{spec}</code>
      </p>
      <p>
        This module is locked behind <code>{gate}</code>. Implementation begins once Phase 0
        exit criteria are met (see <code>MASTER_PLAN.md</code>) and the corresponding ADR is
        Accepted.
      </p>
      {children}
    </section>
  );
}
