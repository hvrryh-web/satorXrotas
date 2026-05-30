/**
 * Lane A (Task A5 + A6) — Focus Hero module entry.
 *
 * `/focus` renders the home view (mode picker + recent sessions); when
 * a session is running it switches to the full-screen Active view.
 */

import { useState } from 'react';
import { FocusHome } from './FocusHome';
import { FocusActive } from './FocusActive';
import type { SessionMode } from '@njz-os/focus-engine';

export function FocusRoute() {
  const [activeMode, setActiveMode] = useState<SessionMode | null>(null);
  if (activeMode) {
    return <FocusActive mode={activeMode} onExit={() => setActiveMode(null)} />;
  }
  return <FocusHome onStart={setActiveMode} />;
}
