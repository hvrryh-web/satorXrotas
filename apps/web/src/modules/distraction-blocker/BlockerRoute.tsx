import { PhaseStub } from '@/shared/PhaseStub';

export function BlockerRoute() {
  return (
    <PhaseStub
      module="Distraction Blocker"
      gate="G1.blocker"
      phase={1}
      spec="docs/prototype-systems/PS-003-distraction-blocker.md"
    />
  );
}
