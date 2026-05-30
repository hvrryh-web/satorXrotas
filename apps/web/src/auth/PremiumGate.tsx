/**
 * Lane E (Task E5) — Premium-route gating helper.
 *
 * Wraps a route element; if the current user lacks the minimum tier,
 * renders a friendly upsell instead. Used by Phase-2 lanes (W/L/B′)
 * for tier-locked features (Historical Trends 30/60/90, premium card
 * themes, etc.).
 */

import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { useRequireTier } from './AuthProvider';
import type { Tier } from '@njz-os/adapters-identity-client';

export function PremiumGate({
  minimum,
  feature,
  children,
}: {
  minimum: Tier;
  feature: string;
  children: ReactNode;
}) {
  const { allowed, current } = useRequireTier(minimum);
  if (allowed) return <>{children}</>;
  return (
    <div className="rat-page rat-page--stub">
      <h1>{feature} is premium</h1>
      <p>
        This feature is available on the <strong>{minimum}</strong> tier and up.
        You&rsquo;re currently on <strong>{current ?? 'unauthenticated'}</strong>.
      </p>
      <p>
        <Link to="/account">Upgrade in account settings</Link>.
      </p>
    </div>
  );
}
