[Ver001.000]

# PS-003 — Distraction Blocker

- **Status:** Draft (Phase 0); flips to Approved when ADR-0009 lands.
- **Owner:** Implementer (Phase 1)
- **Phase:** 1 (web — service worker + service-worker-based blocking on supported routes); Phase 3 (native iOS/Android via Screen Time / DigitalWellbeing APIs)
- **Package:** apps/web (no dedicated `@njz-os/*` package in Phase 1 — keeps logic with the UI surface that owns enforcement)
- **Gate:** `G1.blocker`

## Purpose

Digital discipline tooling. Lets users block apps/sites during focus sessions, with four enforcement levels (Gentle → Moderate → Strict → Maximum). Web-first in Phase 1; native depth in Phase 3.

## Surface (Phase 1)

The webapp registers a service worker with a routes-to-block list. Browsing within RAT-OS during an active block:

- Redirects to `/focus-active` with a motivational screen if the URL matches a block rule.
- Records the attempt to vaultbrain for analytics.

For users with multiple browser tabs, an in-app banner reminds of the active block.

For OS-level blocking (Phase 3), the native shells (Capacitor or RN) integrate the relevant platform API.

## Domain Types

- `BlockerSettings`, `BlockSchedule`, `EnforcementLevel`, `BlockAttempt` (`@njz-os/focus-engine/src/blocker.ts` — even though it's primarily an app concern, the type lives in the focus engine because schedules tie into focus sessions).

## Integration Points

- **Focus Hero:** active focus session auto-activates blocker if user opts in.
- **Calendar adapter (Phase 2+):** auto-block during Focus / Deep Work / Study events.
- **Vaultbrain:** persist block list, schedule, attempt log.
- **PolyCo.World:** active blocker visualises as Shield Room glow; streaks unlock Iron Will and Fortress.

## Risks

- **Service worker scope limits.** Can only block navigation within the RAT-OS origin in Phase 1. Real cross-site blocking is a Phase 3 native capability. Honest in marketing copy.
- **Override abuse.** Users can disable the blocker; "Strict" / "Maximum" need to be obviously strict without trapping users. Mitigation: cooldown + override count + clear escape valve.
- **iOS app-store policy on blocker apps.** Strict review category. Mitigation: Phase 3 design includes Apple-compliant Screen Time API use.

## Verification

- Unit: schedule resolver (does a given timestamp fall in any active block?).
- Integration: service worker intercepts a fetch to `youtube.com` during active block and redirects.
- E2E: end-to-end session: schedule a 5-min block, attempt to navigate, see redirect, attempt count increments in vaultbrain.

## Out of Scope (Phase 1)

- iOS / Android native blocking — Phase 3.
- App-uninstall protection — Phase 3 (native concern).
- Browser extension as an enforcement vector — under consideration for Phase 2.
- Network-level (DNS / VPN) blocking — out of scope entirely.

## References

- PRD §3.3.
- ADR-0009 (blocker enforcement model — TBD).
- Upstream `notbleaux/ZeSporteXte/apps/browser-extension/` for prior art on extension-based blocking.
