/**
 * Lane E (Task E6) — Onboarding route.
 *
 * Public wrapper around <OnboardingWizard> for the React Router config.
 */

import { OnboardingWizard } from './OnboardingWizard';

export function OnboardingRoute() {
  return <OnboardingWizard />;
}
