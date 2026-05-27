[Ver001.000]

# ADR-0011 — Distraction Blocker Enforcement Model (Web SW + Browser Extension; Native Deferred)

- **Status:** Accepted
- **Date:** 2026-05-24
- **Deciders:** @hvrryh-web
- **Tags:** blocker, service-worker, browser-extension, focus, manifest-v3
- **Protects gate:** `G1.blocker`

## Context

PS-003 (Distraction Blocker) calls for blocking distracting apps and websites during focus sessions with four enforcement levels (Gentle / Moderate / Strict / Maximum). PRD §3.3 documents the target competitor surface: Freedom (cross-platform), Cold Turkey (desktop), Opal (mobile). Phase 1 is web-first; Phase 3 adds native iOS/Android.

The honest truth about web-based blocking:

- A **service worker** scoped to `apps/web` can intercept fetches/navigations *within the RAT-OS origin only*. It cannot block `youtube.com` from being opened in a different tab — that's outside its scope by design (security model).
- The **only** Phase-1 web mechanism that can block cross-origin destinations is a **browser extension** (Chrome MV3, Firefox WebExtensions). Extensions can use `declarativeNetRequest` to block requests to arbitrary hosts.
- iOS Screen Time / Android DigitalWellbeing require a **native app shell** (Phase 3).

We must be honest in marketing copy too — promising "block YouTube" while shipping only a service-worker scope would be a trust failure.

## Decision

Ship a **two-tier Phase-1 blocker**:

### Tier 1 — In-app blocker (always-on, no install required)

Service worker registered by `apps/web/src/sw.ts` (when `pwa-shell` lands per ADR-0005's follow-on work) and a runtime guard inside the SPA:

- During an **active focus session** with blocker armed, any in-app navigation to a route tagged `distraction` is redirected to `/focus-active`.
- Any in-app link (`<a href="…">` to an external host) is intercepted; an interstitial confirms before opening.
- Block attempts are logged via `packages/adapters/vaultbrain-client` → `progression_events` (per ADR-0008 schema) for the user's focus dashboard.

This tier is the **minimum bar**. It catches accidental drift inside RAT-OS itself and produces the analytics that make the Focus Score real (PRD §3.3.6).

### Tier 2 — Companion browser extension (opt-in, true cross-origin blocking)

A Chrome MV3 extension under `apps/browser-extension/` (Phase 1 deliverable; mirrors the existing upstream pattern at `notbleaux/ZeSporteXte/apps/browser-extension/` but RAT-OS-flavoured):

- Listens via a content-script bridge for **active block windows** broadcast by `apps/web` (over `chrome.runtime.connect` once paired) — or polls the vaultbrain API directly if paired with a user account.
- Uses `declarativeNetRequest` rules generated from the user's block list to intercept requests to known distraction hosts.
- Shows a full-screen blocking page with motivational copy + session progress; mirrors the in-app interstitial.
- Logs block attempts back to vaultbrain via the same adapter (auth via OAuth-style flow with the user's RAT-OS session).

Firefox WebExtensions follow once Chrome MV3 ships.

### Enforcement levels (web)

| Level | Tier-1 behaviour | Tier-2 behaviour |
|-------|------------------|------------------|
| Gentle | Notification on attempted in-app distraction; dismissible. | Notification only; no block. |
| Moderate | 10 s delay before allowing in-app distraction. | 10 s delay; reflection prompt. |
| Strict | Hard redirect to `/focus-active`; no in-app override. | Hard block; override locked behind 60 s cooldown + confirmation text input. |
| Maximum | Same as Strict + disables in-app override entirely; uninstall protection is a no-op on web. | Same as Strict + extension self-uninstall is locked during active session via chrome.management API. |

### Schedule resolver

`packages/@njz-os/focus-engine/src/blocker.ts` already declares `BlockSchedule` types. Phase 1 implements:

- `recurring-daily` and `recurring-weekly` resolved via a cron-like evaluator over the user's timezone.
- `one-time` for explicit calendar entries.
- `focus-sync` auto-arms the blocker whenever a `FocusSession` enters state `running`.
- `smart` deferred to Phase 4 (requires usage-pattern data).

### Calendar integration shell

Read-only OAuth to Google Calendar + Apple Calendar (CalDAV). Tagged events (`Focus`, `Deep Work`, `Study`) auto-create `one-time` schedules. Read-only — RAT-OS never writes to user calendars.

### Native deferred (Phase 3)

iOS uses `Family Controls` + `ManagedSettings`. Android uses `UsageStatsManager` + `DevicePolicyManager`. Both require native shell apps (Capacitor or React Native, decision in ADR-0013-or-later). Out of Phase 1 scope.

## Consequences

**Positive:**

- Tier 1 ships with the webapp; no install friction; produces useful analytics from day one.
- Tier 2 is the credible cross-origin story; matches Freedom-class capabilities for power users willing to install.
- Honest marketing copy: "Block in-app distractions with the webapp; install the extension for cross-site blocking; native blocking coming in Phase 3."
- Pattern reuses the upstream `apps/browser-extension/` scaffold — engineering work concentrates on RAT-OS-flavoured UX, not extension plumbing.
- `declarativeNetRequest` is the modern MV3 API; future-proof vs the deprecated `webRequest` blocking interception.

**Negative:**

- Two surfaces to maintain (webapp + extension). Mitigated by sharing block-list and analytics adapters across both.
- Chrome MV3 extension review can take 1–3 weeks at first submission; build into the Phase-1 timeline.
- Maximum-level "uninstall protection" is genuinely impossible on web. Documented honestly in product copy.
- Calendar OAuth scope expands the auth surface; ADR-0013 must accommodate this.

**Neutral:**

- Firefox + Edge + Safari extensions follow standard MV3 portability — small additional work per browser.
- Mobile browsers (iOS Safari, Android Chrome) generally don't support extensions; for Phase 1 those users have Tier 1 only.

## Alternatives Considered

- **Service worker only.** Rejected: cannot block cross-origin. Would force dishonest marketing.
- **VPN / DNS-level blocking** (e.g., NextDNS or a custom proxy). Rejected: outside our trust boundary, requires user network reconfiguration, fights with corporate VPNs. Out of scope entirely.
- **Browser extension only (skip Tier 1).** Rejected: install friction for the majority of users; loses the in-app analytics value.
- **Native shells from day one (Phase 3 → Phase 1).** Rejected: doubles Phase 1 surface; iOS Family Controls approval is multi-week; deferring is correct per the PRD's phase plan.
- **Manifest V2** instead of V3. Rejected: Chrome is removing MV2 support; building anything new on MV2 is malpractice.

## Related

- ADR-0008 — Vaultbrain integration shape (block attempts persisted via the adapter).
- ADR-0009 — Focus Engine state machine (`focus-sync` block schedule subscribes to FocusSession state).
- ADR-0013 (planned) — Auth model (OAuth flow shared with calendar integration here).
- `docs/prototype-systems/PS-003-distraction-blocker.md` — module spec.
- `packages/@njz-os/focus-engine/src/blocker.ts` — domain types already defined.
- `apps/browser-extension/` (new path, Phase 1) — Chrome MV3 extension package.
- Upstream reference: `notbleaux/ZeSporteXte/apps/browser-extension/`.

---

> When proposing, leave Status: Proposed. On approval, change to Accepted in a follow-up commit.
> Append a one-line entry to `.agents/DECISION_LOG.md` referencing this ADR.
