/**
 * Lane B Task B7 — Soundscapes module entry.
 *
 * /sound shows category tiles; selecting one navigates to a per-scape
 * active player (SoundActive). State stays local to the module; the
 * audio engine is constructed lazily on first user gesture (per iOS
 * audio-context policy).
 */

import { useState } from 'react';
import { SoundHome } from './SoundHome';
import { SoundActive } from './SoundActive';
import type { Soundscape } from '@njz-os/audio-engine';

export function SoundRoute() {
  const [active, setActive] = useState<Soundscape | null>(null);
  if (active) {
    return <SoundActive soundscape={active} onExit={() => setActive(null)} />;
  }
  return <SoundHome onSelect={setActive} />;
}
