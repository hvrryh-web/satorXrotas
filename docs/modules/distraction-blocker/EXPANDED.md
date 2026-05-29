[Ver001.000]

# Distraction Blocker — Expanded Module Documentation

> **Lane D** in Stage 3 of the next-stages plan. Implementation-ready spec.

## 1. Module identity & scope

| Field | Value |
|-------|-------|
| **Module name** | Distraction Blocker (Web SW + Chrome MV3 extension) |
| **Slug (code)** | `distraction-blocker` |
| **Status** | Documented (Accepted); implementation pending; **Wave D.2** in execution plan (gated on Lane E E5 signal) |
| **Owner role** | Implementer + Critic |
| **Channel** | `web-app` + new `apps/browser-extension/` |
| **Gate protected** | `G1.blocker` (currently LOCKED) |
| **Phase** | 1 (web SW + Chrome MV3) → 3 (native iOS Family Controls + Android DigitalWellbeing) |
| **Source ADRs** | ADR-0011 (Distraction Blocker enforcement model) |
| **Source PS** | `docs/prototype-systems/PS-003-distraction-blocker.md` |
| **Parent docs** | PRD §3.3, ROOT_AXIOMS PR-03 (trust & privacy) |
| **Plan reference** | Lane D in `.agents/session-workplans/SW-20260524-stage-3-lanes.md` |

The Distraction Blocker is the cognitive-discipline tool. Per ADR-0011 it
ships in **two tiers** for Phase 1:

- **Tier 1 (always-on, no install):** in-app service worker scoped to
  `apps/web` intercepts navigations *within the RAT-OS origin* to
  routes the user has tagged as distracting (in-app block list +
  calendar-driven schedule). Cannot block external sites.
- **Tier 2 (opt-in install):** Chrome MV3 browser extension using
  `declarativeNetRequest` to block cross-origin URLs. Pairs with the
  webapp via `chrome.runtime.connect`.

Honest marketing copy is non-negotiable: PS-003 §"Out of scope" mandates
that Tier 1's scope (RAT-OS origin only) is surfaced to users. Native
iOS/Android Screen Time / DigitalWellbeing integrations are explicitly
deferred to Phase 3.

Three structural properties:

1. **Two-tier with graceful degradation.** Tier 1 works for everyone;
   Tier 2 amplifies for users who install the extension. Marketing
   doesn't promise cross-origin blocking without the extension.
2. **Calendar-driven scheduling.** Google Calendar + Apple Calendar
   (CalDAV) read-only OAuth; events tagged `Focus`, `Deep Work`, `Study`
   auto-create blocker schedules.
3. **Focus-sync.** When a `FocusSession` enters `running` (via Lane A's
   `useFocusSession`), the blocker auto-arms with the user's default
   block list; on `completed`/`abandoned`, it disarms.

## 2. Architecture

```
apps/web/src/
  ├─ sw.ts                         Service worker (Tier 1)
  ├─ modules/distraction-blocker/
  │   ├─ BlockerRoute.tsx          (was PhaseStub)
  │   ├─ Home.tsx                  Block-list categories + custom URLs
  │   ├─ Schedule.tsx              Recurring/one-time/focus-sync UI
  │   ├─ FocusScore.tsx            Daily/weekly Focus Score viz
  │   ├─ BlockedInterstitial.tsx   Full-screen "session in progress" page
  │   └─ components/
  │       ├─ CategoryToggle.tsx
  │       ├─ LevelPicker.tsx (Gentle/Moderate/Strict/Maximum)
  │       └─ HeatMap.tsx           Attempts by day × hour

apps/browser-extension/             NEW workspace package (Tier 2)
  ├─ manifest.json                 MV3 manifest
  ├─ background.ts                 Service-worker entry (extension bg)
  ├─ content.ts                    Content script (bridges to RAT-OS)
  ├─ options.html + options.ts     Settings page
  └─ pages/blocked.html            Full-page block screen

packages/@njz-os/focus-engine/src/
  └─ blocker.ts                    (existing types; extend with resolver)

packages/adapters/calendar-client/  NEW (or extends identity-client)
  └─ src/index.ts                  Google + Apple Calendar OAuth
```

Key trade-offs from ADR-0011:

- `declarativeNetRequest` (MV3) over deprecated `webRequest` blocking.
- Chrome MV3 first; Firefox WebExtensions follows once Chrome ships.
- Native iOS/Android deferred — Family Controls / DigitalWellbeing each
  need a native shell (Phase 3).
- Calendar OAuth is **read-only**; we never write to user calendars.

Architecture extensions for impl:

- **Schedule evaluator** as a pure function over timestamp + user's tz
  + schedule list. Easy to unit-test against DST and cross-midnight
  cases.
- **Bridge protocol** between webapp and extension: `chrome.runtime
  .connect()` with a versioned JSON-RPC channel. Bumping protocol
  version triggers a "please update the extension" UI banner.
- **Override accounting** server-side via vaultbrain
  `progression_events` (`blocker.override.used`). Cooldown enforcement
  client-side (60 s default).

## 3. Domain types & contracts

### Block schedule (per Phase 0 stub + extensions)

```ts
// packages/@njz-os/focus-engine/src/blocker.ts (extend stub)
export type EnforcementLevel = 'gentle' | 'moderate' | 'strict' | 'maximum';

export interface BlockerSettings {
  enforcementLevel: EnforcementLevel;
  whitelist: string[];                   // app/site identifiers allowed during blocks
  overrideCooldownSeconds: number;       // default 60
  overrideLimitPerDay: number;           // default 3
  blockCategories: BlockCategory[];
  customHosts: string[];                 // user-added URL patterns (wildcards supported)
}

export type BlockCategory = 'social' | 'entertainment' | 'messaging' | 'shopping' | 'news' | 'games';

export const CATEGORY_HOSTS: Record<BlockCategory, string[]> = {
  social:        ['instagram.com', 'tiktok.com', 'twitter.com', 'x.com', 'facebook.com', 'snapchat.com', 'reddit.com'],
  entertainment: ['youtube.com', 'netflix.com', 'twitch.tv'],
  messaging:     ['whatsapp.com', 'telegram.org', 'discord.com'],
  shopping:      ['amazon.com', 'ebay.com'],
  news:          ['cnn.com', 'bbc.com', 'foxnews.com'],
  games:         /* auto-detected by extension at install time */ [],
};

export type ScheduleKind = 'recurring-daily' | 'recurring-weekly' | 'one-time' | 'focus-sync' | 'smart';

export interface BlockSchedule {
  id: string;
  kind: ScheduleKind;
  startsAt: string;        // ISO 8601 (one-time) or HH:MM (recurring)
  durationMs: number;
  daysOfWeek?: number[];   // 0–6 for recurring-weekly
  source?: 'calendar' | 'user' | 'focus-engine';
  sourceRef?: string;      // calendar event id, focus session id
}

export interface BlockAttempt {
  id: string;
  at: string;
  url: string;
  scheduleId: string;
  overridden: boolean;
  tier: 1 | 2;             // which tier blocked it
}
```

### Schedule evaluator

```ts
// packages/@njz-os/focus-engine/src/schedule-resolver.ts (new)
export function isBlockedAt(
  schedules: BlockSchedule[],
  timestamp: Date,
  tz: string,
): { blocked: boolean; activeSchedule?: BlockSchedule } {
  // Convert timestamp to user's tz; evaluate each schedule
}
```

Tests cover:

- DST spring-forward (lose an hour mid-block)
- DST fall-back (double-block)
- Cross-midnight schedules (start 23:00 + duration 2h)
- One-time event in the past (skipped)
- Focus-sync activates immediately when FocusSession enters `running`

### Service worker contract (Tier 1)

```ts
// apps/web/src/sw.ts (new)
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));

self.addEventListener('fetch', (event: FetchEvent) => {
  const url = new URL(event.request.url);
  // Only intercept same-origin navigations
  if (url.origin !== self.location.origin) return;
  if (event.request.mode !== 'navigate') return;

  const isBlockedRoute = checkBlockList(url.pathname);
  if (isBlockedRoute && isCurrentlyBlocked()) {
    event.respondWith(Response.redirect('/blocked', 302));
    void logAttempt(url, 1);
  }
});
```

### Browser extension contract (Tier 2)

```jsonc
// apps/browser-extension/manifest.json
{
  "manifest_version": 3,
  "name": "NJZ RAT-OS Blocker",
  "version": "0.1.0",
  "permissions": ["declarativeNetRequest", "storage", "alarms"],
  "host_permissions": ["<all_urls>"],
  "background": { "service_worker": "background.js" },
  "content_scripts": [{
    "matches": ["https://app.njz-rat-os.app/*", "http://localhost:5173/*"],
    "js": ["content.js"]
  }],
  "options_page": "options.html",
  "declarative_net_request": {
    "rule_resources": [{ "id": "user-block-list", "enabled": true, "path": "rules.json" }]
  }
}
```

Bridge protocol (RAT-OS webapp ↔ extension):

```ts
type BridgeMsg =
  | { kind: 'BLOCK_LIST_UPDATE'; rules: chrome.declarativeNetRequest.Rule[] }
  | { kind: 'SCHEDULE_ARM'; schedule: BlockSchedule }
  | { kind: 'SCHEDULE_DISARM'; scheduleId: string }
  | { kind: 'ATTEMPT_LOGGED'; attempt: BlockAttempt };
```

### Calendar adapter

```ts
// packages/adapters/calendar-client/src/index.ts (new)
export interface CalendarEvent {
  id: string;
  title: string;
  startsAt: string;
  endsAt: string;
  tags: string[];           // 'Focus', 'Deep Work', 'Study', ...
}

export interface CalendarClient {
  listEvents(opts: { from: Date; to: Date }): Promise<CalendarEvent[]>;
  subscribe(handler: (events: CalendarEvent[]) => void): () => void;
}
```

Uses Lane E's auth surface for OAuth bootstrap; Google + Apple
CalDAV both read-only.

### Vaultbrain endpoints (per ADR-0008 surface)

| Endpoint | When |
|----------|------|
| `POST /users/{id}/blocker/attempt` | each block intercept (Tier 1 or 2) |
| `GET /users/{id}/blocker/attempts?from=&to=` | HeatMap mount |
| `POST /users/{id}/blocker/override` | when user invokes override (with cooldown enforcement) |
| `GET /users/{id}/blocker/settings` | settings hydration |
| `PUT /users/{id}/blocker/settings` | user updates settings |

These extend the `progression_events` table for attempts; settings live
in a new `blocker_settings` table (Phase 1) or in vaultbrain notes
(Phase 0 fallback).

## 4. Implementation walkthrough — task by task

### Task D1 — Schedule resolver

`packages/@njz-os/focus-engine/src/schedule-resolver.ts`. Use `date-fns-tz`
for timezone-aware comparisons.

Vitest covers ≥ 6 cases per §3 list. DST cases use `date-fns-tz`'s
zoned-time helpers.

Commit: `feat(blocker): schedule resolver with DST + cross-midnight tests`.

### Task D2 — Service worker enforcement (Tier 1)

`apps/web/src/sw.ts` (see §3 contract). Register via Vite PWA plugin or
minimal SW setup. Add `apps/web/src/sw-register.ts` called from main.

`/blocked` route renders a motivational interstitial showing remaining
session time + "Override (60 s cooldown)" button + Focus Score impact
warning.

Tests: Playwright with SW context enabled — schedule a block, attempt to
navigate, see redirect; assert vaultbrain receives one attempt.

Commit: `feat(blocker): service-worker enforcement + interstitial`.

### Task D3 — Block-list UI

Replace `BlockerRoute.tsx` PhaseStub with `Home.tsx`:

```tsx
export function BlockerRoute() {
  const { settings, updateSettings } = useBlockerSettings();
  return (
    <section className="rat-page">
      <h1>Distraction Blocker</h1>
      <LevelPicker value={settings.enforcementLevel} onChange={(v) => updateSettings({ enforcementLevel: v })} />
      <h2>Categories</h2>
      {(Object.keys(CATEGORY_HOSTS) as BlockCategory[]).map((cat) =>
        <CategoryToggle key={cat} category={cat} enabled={settings.blockCategories.includes(cat)} />
      )}
      <h2>Custom URLs</h2>
      <CustomHostInput hosts={settings.customHosts} onChange={(hosts) => updateSettings({ customHosts: hosts })} />
      <h2>Schedules</h2>
      <Schedule />
      <h2>Focus Score (last 7 days)</h2>
      <FocusScore />
      <HeatMap />
    </section>
  );
}
```

`LevelPicker` shows behaviour preview per level (Gentle → notification;
Strict → no override possible). UI copy must explain Tier 1 / Tier 2
honestly: "Install the browser extension to block sites outside RAT-OS."

Commit: `feat(web/blocker): block-list UI with category toggles`.

### Task D4 — Browser extension (Tier 2)

Scaffold `apps/browser-extension/` workspace package. Add to
`pnpm-workspace.yaml` if needed. MV3 manifest, background SW, content
script, options page, blocked page.

Background SW maintains the `declarativeNetRequest` rule set, derived
from settings pulled via the bridge from RAT-OS webapp. On rule update,
calls `chrome.declarativeNetRequest.updateDynamicRules`.

Tests: headless Chromium "Load unpacked" + Playwright assertions on
blocked navigation.

Commit: `feat(blocker): Chrome MV3 extension (apps/browser-extension)`.

### Task D5 — Calendar integration shell

`packages/adapters/calendar-client/` — Google Calendar (read-only OAuth
scope `calendar.readonly`) + Apple Calendar via CalDAV.

Lane E's auth surface bootstraps the OAuth flow; the calendar adapter
handles token refresh + event listing. Events tagged `Focus`, `Deep
Work`, `Study` (per PS-003) auto-create `one-time` schedules with
`source: 'calendar'` + `sourceRef: <eventId>`.

Pre-session notification: 5 min before a calendar-derived block window,
surface a toast in RAT-OS: "Focus block starting in 5 min."

Commit: `feat(blocker): calendar OAuth + auto-schedule from events`.

### Task D6 — Focus-engine coupling + analytics

`useFocusSession` exposes its state. The blocker subscribes:

```ts
useEffect(() => {
  if (focusSession.state === 'running') armSchedule({ id: 'focus-sync-current', kind: 'focus-sync', startsAt: new Date().toISOString(), durationMs: focusSession.totalMs, source: 'focus-engine', sourceRef: focusSession.id });
  if (focusSession.state === 'completed' || focusSession.state === 'abandoned') disarmSchedule('focus-sync-current');
}, [focusSession.state]);
```

**Focus Score** (0–100) per PS-003 §3.3.6:

```
FocusScore = max(0, 100 - attempts × 5 + overrides × -20 + completionRate × 30)
```

Where `completionRate` = sessions completed / sessions started in the
window. Rendered in `FocusScore.tsx` with daily/weekly trend.

`HeatMap.tsx` shows attempts as a day × hour grid (calendar heat map),
sourced from `GET /users/{id}/blocker/attempts`.

Commit: `feat(blocker): focus-engine coupling + Focus Score + HeatMap`.

### Task D7 — Tests + extension submission + gate flip (orchestrator)

Full E2E in Playwright: schedule → navigation attempt → interstitial →
vaultbrain log inserted. Chrome Web Store submission flagged early in
the plan (1–3 week review tail).

A8-style gate flip reserved for orchestrator.

## 5. Telemetry & analytics events

| Event `kind` | When | Payload |
|--------------|------|---------|
| `blocker.schedule.armed` | schedule active (manual or auto) | `{ userId, scheduleId, kind, source }` |
| `blocker.schedule.disarmed` | schedule ends or user disarms | `{ userId, scheduleId, reason }` |
| `blocker.attempt` | block intercept | `{ userId, scheduleId, url, tier, at }` |
| `blocker.override.used` | user invokes override | `{ userId, scheduleId, at, remainingForDay }` |
| `blocker.session.complete` | block window naturally ends | `{ userId, scheduleId, attempts, overrides, focusScore }` |

OKR mapping:

- **O1.1 KR1** — schedule.armed daily count proxies engagement.
- PRD §2.3.2 module engagement target — "Distraction Blocker 35% of DAU @ Month 6".
- Focus Score is a quality metric reportable to user (no OKR mapping).

## 6. Test plan

| Tier | Tooling | Target |
|------|---------|--------|
| Unit | Vitest + date-fns-tz | schedule resolver ≥ 6 DST/cross-midnight cases |
| Unit | Vitest | Focus Score formula correctness |
| Integration | Vitest + msw | calendar adapter mocks Google + CalDAV |
| E2E | Playwright (SW context) | full Tier 1 block flow |
| E2E | Playwright + headless Chromium "Load unpacked" | full Tier 2 block flow |
| Cross-browser | Playwright (Chromium, Firefox) | Tier 1 SW works everywhere; Tier 2 Chromium-only |
| Manual | iPhone 12 + mid-range Android | Tier 1 only on mobile (no extension); honest copy verified |
| a11y | axe | block-list UI; interstitial keyboard-navigable |
| Perf | Lighthouse | ≥ 85 on `/blocker` route |

## 7. Accessibility plan

| Component | Requirement |
|-----------|-------------|
| `CategoryToggle` | Native `<input type="checkbox">`; label associated; ≥ 44 px tap target |
| `LevelPicker` | Radio group with `fieldset` + `legend`; behaviour preview screen-reader friendly |
| `HeatMap` | Data also exposed as a `<table>` alternative for screen readers |
| `BlockedInterstitial` | `aria-live="assertive"` announcement: "Distraction blocked. 23 minutes remaining."; Override button focusable; Esc returns to active session |
| Override confirmation | Native `<dialog>`; focus trap; type-to-confirm input (e.g. "I choose to break my focus") for Strict level |
| Reduced motion | Disable HeatMap pulse animations |
| Color contrast | Heat-map cells ≥ 3:1 minimum across all intensities |
| Honest copy | Tier 1 vs Tier 2 capability difference plainly stated, not buried |

## 8. Risk register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Tier 1 marketed as if it blocks cross-origin → user trust failure | H | H | Copy review per ROOT_AXIOMS PR-03; "RAT-OS routes only" badge on Tier 1 |
| Chrome Web Store review delays Tier 2 launch | H | M | Submit at start of Phase 1; Phase 1 can ship with Tier 1 only |
| MV3 policy changes deprecate `declarativeNetRequest` features | L | M | Pin to MV3 baseline; monitor Chrome release notes |
| Service worker registration breaks SPA routing | M | M | Test with Playwright SW context; clear SW cache on extension update |
| Calendar OAuth scopes too broad → privacy concern | M | H | Read-only `calendar.readonly` scope only; documented in SECURITY.md |
| Override loophole bypassed via dev tools (un-register SW) | H | L | Phase 1 trust model: blocker is a tool, not a fortress. Maximum level surfaces this. |
| Focus Score formula feels punitive | M | M | Phase 1 tuned conservatively; monitor user feedback; adjust in Phase 2 |
| Cross-tab override count race | L | L | Vaultbrain enforces server-side cooldown; client UI is hint only |

## 9. Cross-lane handoffs

| Direction | What | Counterparty |
|-----------|------|--------------|
| **Consumes** auth state | userId, OAuth bootstrap for calendar | Lane E |
| **Consumes** FocusSession state | `useFocusSession()` for focus-sync arming | Lane A |
| **Consumes** ProgressionEvent stream | display attempts + overrides correctly across devices | Lane C (event-derived scene; not directly here, but the same event-log pattern) |
| **Emits** `blocker.*` events | New event names in canonical taxonomy | Lane F |
| **Consumes** identity-client | calendar OAuth flow piggybacks Supabase session | Lane E ADR-0013 |

## 10. Out of scope

- iOS Family Controls / Android DigitalWellbeing — Phase 3 (native shell).
- Browser extensions for Firefox / Safari / Edge — Phase 2 (MV3 portable).
- Network-level / DNS / VPN blocking — never (outside trust boundary).
- App-uninstall protection on web — impossible (honest copy).
- Smart schedule (AI-suggested blocks from usage) — Phase 4.

## 11. Open questions / TODOs for implementation

| Question | Options | Recommended default | Decision owner |
|----------|---------|---------------------|-----------------|
| Where do extension settings live — extension storage or vaultbrain? | (a) extension only (b) vaultbrain (synced) | (b) — single source of truth; extension reads via bridge | Architect |
| How does the extension authenticate as the user? | (a) shared Supabase JWT (b) extension-specific token | (a) Phase 1; revisit if Chrome Web Store flags it | Security |
| Tier 1 interstitial — full-screen takeover or modal? | (a) full-screen route (b) modal | (a) — harder to dismiss accidentally | Designer |
| What happens to scheduled blocks if user signs out mid-window? | (a) schedules disarm on sign-out (b) persist | (a) — privacy + correctness | Security |
| Calendar tag matching — case-sensitive? | (a) exact (b) case-insensitive | (b) — "Focus" / "focus" / "FOCUS" all match | Implementer |
| Focus Score formula tuning — should we surface the formula to users? | (a) yes (b) no | (a) — transparency builds trust | Designer |
| Phase 1 extension distribution — Chrome Web Store or direct CRX? | (a) Store only (b) Store + direct | (a) — Store provides discoverability + auto-update | Platform |

---

> **When implementing**, all marketing copy on `/blocker` and the
> marketing site must clearly state Tier 1 ("blocks RAT-OS routes")
> vs Tier 2 ("blocks any site, install the extension"). PR review
> should check this.

> **See also:** ADR-0011, PS-003, `packages/@njz-os/focus-engine/src/blocker.ts`, `apps/browser-extension/` (new), ROOT_AXIOMS PR-03.
