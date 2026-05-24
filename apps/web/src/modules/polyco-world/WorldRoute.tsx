import { PhaseStub } from '@/shared/PhaseStub';

export function WorldRoute() {
  return (
    <PhaseStub
      module="PolyCo.World"
      gate="G1.polyworld-office"
      phase={1}
      spec="docs/prototype-systems/PS-007-polyco-world.md"
    >
      <p>
        Office shell ships first (Phase 1); Home module (Phase 2); social features (Phase 3).
      </p>
    </PhaseStub>
  );
}
