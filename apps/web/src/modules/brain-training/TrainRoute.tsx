import { PhaseStub } from '@/shared/PhaseStub';

export function TrainRoute() {
  return (
    <PhaseStub
      module="Brain Training"
      gate="G2.brain-training"
      phase={2}
      spec="docs/prototype-systems/PS-006-brain-training.md"
    />
  );
}
