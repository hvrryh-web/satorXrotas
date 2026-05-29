[Ver001.000]

# Marketing Site + Auth + Onboarding — Expanded Module Documentation

> **Lane E** in Stage 3 of the next-stages plan. Cross-cutting module —
> first-impression surface + auth backbone + onboarding wizard. Critical
> path: **Lane E gates Lane D Wave 2** via the E5 webapp-auth signal.

## 1. Module identity & scope

| Field | Value |
|-------|-------|
| **Module name** | Site + Auth + Onboarding |
| **Slug (code)** | `auth-and-site` (filesystem); spans `apps/site/`, `apps/web/src/auth/`, `apps/web/src/onboarding/`, `apps/web/src/account/`, `packages/adapters/identity-client/` |
| **Status** | Documented (Accepted); implementation pending |
| **Owner role** | Implementer + Security + Designer |
| **Channel** | `site` + `web-app` |
| **Gates protected** | New `G1.webapp-auth` (to be added); `G2.premium` (Phase 2; this lane lays groundwork) |
| **Phase** | 1 (full marketing content + Supabase Auth + 3-step onboarding) → 2 (premium billing tier upgrade) → 3 (OAuth providers expansion) |
| **Source ADRs** | ADR-0004 (apps/site + apps/web split), ADR-0013 (Auth model — passkeys + Supabase) |
| **Source PS** | None (cross-cutting; not a single PS) |
| **Parent docs** | PRD §1, §2, §7; PERSONAS.md; PRICING.md; ROOT_AXIOMS PR-03 (trust & privacy), CONTEXT_SECURITY.md |
| **Plan reference** | Lane E in `.agents/session-workplans/SW-20260524-stage-3-lanes.md` |

Lane E is **the most cross-cutting Phase-1 lane**. It builds:

1. The full marketing site content (`apps/site/`) — hero, modules grid,
   pricing, about, blog scaffold, SEO/OG metadata.
2. The auth backbone (`packages/adapters/identity-client/`, `apps/web/src/auth/`) —
   Supabase Auth wired with passkeys (WebAuthn) primary + email
   magic-link fallback, HttpOnly cookie session, JWT refresh.
3. The 3-step onboarding wizard (`apps/web/src/onboarding/`) — pick
   primary modules, calibrate frequency, set first weekly goal.
4. Account settings + Right-to-Delete (`apps/web/src/account/`).

**Critical hand-off signal (E5):** when Task E5 (webapp shell + tier check)
lands cleanly, write a clear `E5 DONE — Lane D may launch` line to
`.agents/handoff/lane-e-e5.md`. This unblocks Lane D's calendar OAuth
work since it piggybacks the same Supabase session.

Three structural properties:

1. **Tier source-of-truth in vaultbrain, identity in Supabase.** The
   `users.tier` column lives upstream (per ADR-0008); Supabase carries
   only the auth identity. This separation keeps user-domain data
   ownership clean.
2. **Local-first auth state on the webapp.** `apps/web` reads the JWT
   in memory after hydration; never persists it outside `@supabase/ssr`'s
   HttpOnly cookie.
3. **Right-to-Delete is atomic across Supabase + vaultbrain.** Phase 2's
   `services/rat-os-api` BFF orchestrates the dual deletion; Phase 1
   ships a documented manual flow + a deletion-request endpoint that
   the BFF will eventually implement.

## 2. Architecture

```
apps/site/                              (marketing, Next.js 15)
  └─ src/app/
       ├─ page.tsx                      Hero + 7-module preview
       ├─ pricing/page.tsx
       ├─ modules/[slug]/page.tsx       PS-001..PS-007 dynamic
       ├─ about/page.tsx
       └─ blog/                         MDX scaffold

apps/web/src/
  ├─ auth/                              Phase-1 auth shell
  │   ├─ AuthProvider.tsx               React context; consumes identity-client
  │   ├─ SignIn.tsx                     Passkey-first + email fallback
  │   ├─ PasskeyEnroll.tsx
  │   ├─ tier.ts                        Tier check via vaultbrain
  │   └─ README.md                      Supabase provisioning runbook
  ├─ onboarding/
  │   ├─ Wizard.tsx                     3-step container
  │   ├─ Step1Modules.tsx
  │   ├─ Step2Frequency.tsx             Uses Lane B's binaural engine
  │   └─ Step3Goal.tsx
  └─ account/
       ├─ Settings.tsx
       ├─ DataExport.tsx
       └─ DeleteAccount.tsx

packages/adapters/identity-client/      Phase-0 stub → real Supabase wrapper
  └─ src/index.ts                       Supabase Auth + session helpers
```

Key trade-offs already decided:

- **Supabase Auth** over self-hosted (ADR-0013) — aligns with upstream
  `services/agent-gateway/supabase_mirror.py`; one identity substrate
  across NJZ products.
- **Passkeys primary, email fallback** — no password database.
- **Tier in vaultbrain, identity in Supabase** — separates concerns;
  Supabase metadata is never the source of truth for product tier.
- **`@supabase/ssr`** over the legacy `@supabase/auth-helpers` —
  modern cookie flow; works with Next.js App Router.

Architecture extensions for impl:

- **CSRF defence:** `SameSite=Lax` cookie + double-submit `X-NJZ-CSRF`
  header for state-changing requests. The token rotates on session
  refresh.
- **Tier cache:** TanStack Query cache (60 s stale, 5 min cache) wrapping
  `GET /users/me` from vaultbrain. Premium-gated routes check the tier
  on render; server-side gating happens in the Phase-2 BFF.
- **Onboarding state:** server-persisted (vaultbrain `users.onboarding`
  jsonb) so a user who signs up on mobile and continues on desktop
  picks up where they left off.

## 3. Domain types & contracts

### `identity-client` real surface

```ts
// packages/adapters/identity-client/src/index.ts (replaces stub)
import type { UserId } from '@njz-os/core';

export interface IdentityConfig {
  supabaseUrl: string;
  supabaseAnonKey: string;
}

export interface AuthSession {
  userId: UserId;
  expiresAt: string;
  tier: 'free' | 'premium' | 'team';        // mirrored from vaultbrain users.tier
}

export interface IdentityClient {
  currentSession(): Promise<AuthSession | null>;
  signInWithPasskey(): Promise<AuthSession>;
  signInWithMagicLink(email: string): Promise<{ ok: boolean; messageSent: boolean }>;
  signOut(): Promise<void>;
  enrolPasskey(): Promise<{ credentialId: string }>;
  listPasskeys(): Promise<{ id: string; createdAt: string; lastUsedAt: string }[]>;
  removePasskey(id: string): Promise<void>;
  requestAccountDeletion(): Promise<{ scheduledAt: string }>;
  exportData(): Promise<Blob>;            // CSV + JSON bundle
}

export class IdentityError extends Error {
  constructor(message: string, public readonly code: string) { super(message); this.name = 'IdentityError'; }
}

export function createIdentityClient(config: IdentityConfig): IdentityClient;
```

### Onboarding model

```ts
// apps/web/src/onboarding/types.ts (new)
export interface OnboardingState {
  step: 1 | 2 | 3 | 'complete';
  primaryModules: ModuleSlug[];                              // step 1
  frequencyPreset?: 'delta' | 'theta' | 'alpha' | 'beta' | 'gamma';  // step 2
  weeklyGoal?: { sessionsPerWeek: number; minSessionMinutes: number; };  // step 3
  startedAt: string;
  completedAt?: string;
}
```

Persisted in vaultbrain `users.onboarding` jsonb (Phase 1 extension of
the ADR-0008 schema; coordinate with Lane F's Thread 2 upstream PR).

### Auth context surface (for other lanes to consume)

```tsx
// apps/web/src/auth/AuthProvider.tsx
export function useAuth(): {
  session: AuthSession | null;
  loading: boolean;
  signIn: () => void;     // navigates to /signin
  signOut: () => Promise<void>;
};

export function useTier(): 'free' | 'premium' | 'team' | 'unknown';
```

### Supabase env

```bash
# apps/web/.env.example + apps/site/.env.example
NEXT_PUBLIC_SUPABASE_URL=https://<project>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>
# Server-only (apps/site or Phase-2 BFF):
SUPABASE_SERVICE_ROLE_KEY=<service-role>  # never client-exposed
```

### Vaultbrain endpoints (per ADR-0008)

| Endpoint | Used by |
|----------|---------|
| `GET /users/me` | tier check (cached 60 s) |
| `PUT /users/{id}/onboarding` | onboarding state save |
| `GET /users/{id}/onboarding` | onboarding state hydration |
| `DELETE /users/{id}` | Right-to-Delete (Phase 2 via BFF) |

## 4. Implementation walkthrough — task by task

### Task E1 — Marketing site `/` content build-out

`apps/site/src/app/page.tsx`:

```tsx
import { Hero } from '@/components/Hero';
import { ModulesGrid } from '@/components/ModulesGrid';
import { ThesisSection } from '@/components/ThesisSection';

export const metadata = {
  title: 'NJZ RAT-OS — Train. Focus. Create. Learn. Grow.',
  description: 'One neural operating system. Seven modules. A unified wellness-productivity OS.',
  openGraph: { /* og image, type, locale */ },
  twitter: { card: 'summary_large_image' },
};

export default function HomePage() {
  return <>
    <Hero tagline="Train. Focus. Create. Learn. Grow." />
    <ModulesGrid />
    <ThesisSection />
    <PrimaryCta href="/signup" label="Start free" />
  </>;
}
```

`ModulesGrid` renders 7 cards iterating PS-001..PS-007. Each card →
`/modules/<slug>`.

Commit: `feat(site): hero + module preview grid + thesis section on /`.

### Task E2 — `/pricing` + `/modules/[slug]` + `/about` + `/blog`

`apps/site/src/app/pricing/page.tsx` parses tiers from
`docs/product/PRICING.md` (Markdown to JSX via `@next/mdx` or inline).

`apps/site/src/app/modules/[slug]/page.tsx` uses `generateStaticParams`
+ a slug map keyed by ModuleSlug.

`/about` renders the integration thesis from PRD §1 + ROOT_AXIOMS PR-00.

`/blog` MDX scaffold + first post: `blog/posts/rat-os-thesis.mdx`.

SEO + OpenGraph on every route.

Commit: `feat(site): pricing + module pages + about + blog scaffold`.

### Task E3 — Supabase Auth wiring

```bash
pnpm --filter @njz-os/adapters-identity-client add @supabase/ssr @supabase/supabase-js
pnpm --filter @njz-os/web add @supabase/ssr
pnpm --filter @njz-os/site add @supabase/ssr
```

Replace stub `createIdentityClient`:

```ts
import { createBrowserClient } from '@supabase/ssr';

export function createIdentityClient(config: IdentityConfig): IdentityClient {
  const sb = createBrowserClient(config.supabaseUrl, config.supabaseAnonKey);

  return {
    async currentSession() {
      const { data: { session } } = await sb.auth.getSession();
      if (!session) return null;
      const tier = await fetchTierFromVaultbrain(session.user.id);
      return { userId: session.user.id as UserId, expiresAt: session.expires_at!, tier };
    },
    async signInWithMagicLink(email) {
      const { error } = await sb.auth.signInWithOtp({ email, options: { emailRedirectTo: `${window.location.origin}/auth/callback` } });
      return { ok: !error, messageSent: !error };
    },
    async signInWithPasskey() {
      // Supabase passkey flow via webauthn — uses navigator.credentials.get
      const { data, error } = await sb.auth.signInWithIdToken({ /* WebAuthn assertion */ });
      if (error) throw new IdentityError(error.message, error.code ?? 'PASSKEY_FAIL');
      return /* normalised */;
    },
    async signOut() { await sb.auth.signOut(); },
    async enrolPasskey() { /* navigator.credentials.create */ },
    async listPasskeys() { /* read from Supabase auth.identities */ },
    async removePasskey(id) { /* */ },
    async requestAccountDeletion() {
      // Phase 1: write a request marker; Phase-2 BFF processes
      const { data, error } = await sb.from('account_deletion_requests').insert({ requested_at: new Date().toISOString() });
      if (error) throw new IdentityError(error.message, 'DELETION_REQUEST_FAILED');
      return { scheduledAt: new Date(Date.now() + 30 * 86400_000).toISOString() };
    },
    async exportData() {
      // CSV+JSON bundle of vaultbrain-owned user data
      const res = await fetch('/api/account/export', { credentials: 'include' });
      return res.blob();
    },
  };
}
```

Document Supabase provisioning in `apps/web/src/auth/README.md` (see Task E8).

Commit: `feat(identity): real Supabase Auth wiring`.

### Task E4 — Passkey + email sign-in UX

`apps/web/src/auth/SignIn.tsx`:

```tsx
export function SignIn() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [phase, setPhase] = useState<'passkey' | 'email' | 'sent'>('passkey');

  const tryPasskey = async () => {
    try {
      await identityClient.signInWithPasskey();
      // success → redirect
    } catch {
      setPhase('email');
    }
  };

  const sendMagicLink = async (e) => {
    e.preventDefault();
    await identityClient.signInWithMagicLink(email);
    setPhase('sent');
  };

  if (phase === 'passkey') return (
    <section>
      <h1>Sign in with your face</h1>
      <button onClick={tryPasskey}>Use passkey</button>
      <button onClick={() => setPhase('email')}>Use email instead</button>
    </section>
  );
  if (phase === 'email') return (
    <form onSubmit={sendMagicLink}>
      <label>Email <input type="email" value={email} onChange={e => setEmail(e.target.value)} required /></label>
      <button>Send magic link</button>
    </form>
  );
  return <p>Check your email for a sign-in link.</p>;
}
```

`PasskeyEnroll.tsx` prompts on first sign-up + manage-passkeys panel in
account settings.

Commit: `feat(auth): passkey-first sign-in + email magic link UX`.

### Task E5 — Webapp shell + tier check (**Wave D.2 unblock signal**)

`apps/web/src/auth/AuthProvider.tsx`:

```tsx
const AuthCtx = createContext<{ session: AuthSession | null; loading: boolean; /* ... */ }>(/* ... */);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    identityClient.currentSession().then(s => { setSession(s); setLoading(false); });
    // Refresh on Supabase auth state change
    const { data: sub } = supabaseClient.auth.onAuthStateChange((_event, s) => setSession(s as any));
    return () => sub.subscription.unsubscribe();
  }, []);

  return <AuthCtx.Provider value={{ session, loading, /* ... */ }}>{children}</AuthCtx.Provider>;
}

export const useAuth = () => useContext(AuthCtx);
```

`tier.ts`:

```ts
export function useTier(): AuthSession['tier'] | 'unknown' {
  const { session, loading } = useAuth();
  if (loading) return 'unknown';
  return session?.tier ?? 'free';
}
```

Premium gating example:

```tsx
function PremiumOnly({ children }: { children: ReactNode }) {
  const tier = useTier();
  if (tier === 'unknown') return <Loading />;
  if (tier === 'free') return <UpgradePrompt />;
  return <>{children}</>;
}
```

**After this task lands cleanly, append to `.agents/handoff/lane-e-e5.md`:**

```
E5 DONE — Lane D may launch.
Webapp auth surface available:
  - AuthProvider mounted in apps/web/src/main.tsx
  - useAuth() returns { session: AuthSession | null; loading }
  - useTier() returns 'free' | 'premium' | 'team' | 'unknown'
  - identity-client real impl in packages/adapters/identity-client
Lane D's calendar OAuth can now bootstrap from the Supabase session.
```

Commit: `feat(auth): AuthProvider + tier check (Wave D.2 unblock)`.

### Task E6 — 3-step onboarding wizard

`apps/web/src/onboarding/Wizard.tsx`:

```tsx
export function OnboardingWizard() {
  const [state, setState] = useOnboardingState();
  return (
    <main className="onboarding">
      <ProgressIndicator step={state.step} of={3} />
      {state.step === 1 && <Step1Modules state={state} onAdvance={(s) => setState({ ...s, step: 2 })} />}
      {state.step === 2 && <Step2Frequency state={state} onAdvance={(s) => setState({ ...s, step: 3 })} />}
      {state.step === 3 && <Step3Goal state={state} onComplete={() => setState({ ...state, step: 'complete', completedAt: new Date().toISOString() })} />}
    </main>
  );
}
```

`Step1Modules`: multi-select tile grid for the 7 modules (defaults
based on personas).

`Step2Frequency`: short binaural calibration test using Lane B's
`createBinaural()` — plays Alpha for 30 s, asks "calm?", repeats with
Theta + Beta, surfaces the recommended preset. Skippable.

`Step3Goal`: two sliders — sessions/week (1–14) + minimum minutes
(5–90). Surfaces an estimate: "If you hit your goal, you'll complete X
sessions this month."

Persist `OnboardingState` via vaultbrain `PUT /users/{id}/onboarding`
on every step transition. Resumable: `GET /users/{id}/onboarding`
loads on `/onboarding` mount.

Commit: `feat(onboarding): 3-step wizard (modules / frequency / goal)`.

### Task E7 — Account settings + Right-to-Delete

`apps/web/src/account/Settings.tsx`:

- Profile section (display name, email, photo)
- Passkeys section (list + remove + enrol new)
- Connected accounts (Google Calendar — Lane D consumes)
- Data export — CSV + JSON bundle download
- Delete account — confirmation flow

`DeleteAccount.tsx` shows: data that will be deleted, 30-day window,
"Type DELETE to confirm", calls `requestAccountDeletion()`.

Phase 1 ships the request marker + email confirmation; Phase 2's BFF
orchestrates atomic deletion across Supabase + vaultbrain.

Commit: `feat(account): settings + passkey management + Right-to-Delete request`.

### Task E8 — Security review + a11y + launch readiness

`apps/web/src/auth/README.md` documents:

1. Provisioning Supabase preview + prod projects.
2. Env vars to set in Vercel.
3. CSP configuration (per `apps/site/next.config.ts` + `apps/web/vite.config.ts`).
4. detect-secrets baseline.
5. Rotation procedure for `SUPABASE_SERVICE_ROLE_KEY`.

CSP headers (apps/site `next.config.ts`):

```ts
const csp = `
  default-src 'self';
  script-src 'self' 'unsafe-inline' https://*.supabase.co;
  connect-src 'self' https://*.supabase.co wss://*.supabase.co;
  img-src 'self' data: https:;
  style-src 'self' 'unsafe-inline';
  font-src 'self';
  frame-ancestors 'none';
`;
```

Same on apps/web via meta tag (Vite limitation; Phase 2 BFF will set
headers).

WCAG 2.2 AA audit on:

- `/signin`
- `/onboarding`
- `/account/settings`

Add `G1.webapp-auth` row to `.agents/PHASE_GATES.md` (orchestrator-only
final step; do not flip in subagent commit).

Commit: `feat(auth): security review + a11y audit + provisioning README`.

## 5. Telemetry & analytics events

| Event `kind` | When | Payload |
|--------------|------|---------|
| `auth.signup` | Supabase user created via magic-link OR passkey enrol | `{ userId, method, at }` |
| `auth.signin` | Session established | `{ userId, method, at }` |
| `auth.signout` | Explicit sign-out | `{ userId, at }` |
| `onboarding.step.complete` | Each step advances | `{ userId, step, selections }` |
| `onboarding.complete` | Wizard finished | `{ userId, duration_ms, selectedModules, frequencyPreset, weeklyGoal }` |
| `account.deletion.requested` | Right-to-Delete invoked | `{ userId, at, scheduledAt }` |

OKR mapping:

- **O1.1 KR1** — `auth.signup` → MAU bedrock.
- **O1.1 KR5** — onboarding.complete cohort retention is the first
  measurable "engaged Day-1 user" signal.
- **O2.2 KR1** — Phase 2 will add `billing.subscription.start`.

## 6. Test plan

| Tier | Tooling | Target |
|------|---------|--------|
| Unit | Vitest | identity-client error surfaces; tier cache TTL |
| Integration | msw mocking Supabase | sign-in flow end-to-end; passkey enrolment |
| E2E (auth) | Playwright + virtual authenticator | passkey sign-in works in headless Chromium |
| E2E (onboarding) | Playwright | full 3-step wizard completes; state resumes from vaultbrain |
| E2E (deletion) | Playwright | Right-to-Delete request creates marker + email |
| Cross-browser | Playwright (Chromium, Firefox, WebKit) | magic-link works everywhere; passkey on supported only |
| a11y | axe + manual | sign-in + onboarding + settings audit |
| Perf | Lighthouse | ≥ 85 on `/` (apps/site); ≥ 85 on `/onboarding` |
| Security | detect-secrets baseline | no secrets committed |
| Security | manual | CSP headers reach prod; cookie flags Secure+HttpOnly+SameSite=Lax |

## 7. Accessibility plan (WCAG 2.2 AA)

| Component | Requirement |
|-----------|-------------|
| `Hero` | H1 + meaningful tagline; CTA `<button>` keyboard-focusable |
| `ModulesGrid` | Cards as `<a>` with `aria-label` summarising each module |
| `SignIn` | Form labels associated; passkey button keyboard-activates; magic-link email validates HTML5 |
| Passkey enrolment | Native browser UI handles a11y; "What's a passkey?" tooltip readable |
| `OnboardingWizard` | Step progress as `<nav aria-label="Onboarding progress">`; step transitions announce via `aria-live` |
| Step 1 module picker | Multi-select via checkboxes (not custom widget); each checkbox labelled |
| Step 2 frequency calibration | Audio test with visible "Playing Alpha 200 Hz" caption; mute button per safety |
| Step 3 goal sliders | Native `<input type="range">` with `aria-valuemin/max/now` |
| `Settings` | Passkey list as `<ul>` with remove buttons labelled "Remove passkey created on YYYY-MM-DD" |
| Delete flow | Confirmation requires type-to-confirm; screen reader announces consequences |
| CSP | No inline scripts/styles that break SR announcements |

## 8. Risk register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Supabase free tier exhausted before Phase 2 launch | L | M | 50K MAU on free; Phase 1 target 5K MAU; comfortable margin |
| Passkey UX confuses first-time users → drop-off | M | M | Email fallback always available; "What's a passkey?" inline help |
| Hosted Supabase outage blocks all sign-ins | L | H | Open-source `gotrue` is forkable; vaultbrain holds tier truth so degraded mode possible |
| CSP too strict → SignIn breaks | M | M | E2E test asserts SignIn loads under prod CSP |
| Supabase analytics leaks user behaviour | L | L | Disable what we can; document in SECURITY.md; consider self-hosted later |
| Magic-link emails marked spam | M | M | SPF/DKIM/DMARC on production domain; document in provisioning runbook |
| Account-deletion request never processed (Phase 1 lacks BFF) | M | H | Phase 1 sends manual email to operator; Phase 2 BFF processes automatically |
| Onboarding state desync between mobile + desktop | L | L | Server-persisted via vaultbrain; last-write-wins on conflict |
| WebAuthn `rpId` mismatch in preview deploys → passkeys fail | M | L | Separate Supabase preview project with its own `rpId` |
| `users.tier` not yet wired in vaultbrain (ADR-0008 upstream PR pending) | H | M | Phase 1 falls back to `tier: 'free'` for everyone; premium gating defers until upstream lands |

## 9. Cross-lane handoffs

| Direction | What | Counterparty |
|-----------|------|--------------|
| **Provides** auth context via `useAuth()` | Used by every other lane | Lanes A, B, C, D, F |
| **Provides** OAuth bootstrap | Lane D's calendar OAuth piggybacks Supabase session | Lane D Task D5 |
| **Provides** userId | Vaultbrain reads/writes need it | Lanes A, B, C, D |
| **Provides** tier | Premium-gated routes / features | Lanes A, B (Premium soundscapes), C (Premium decorations), D (advanced enforcement) |
| **Provides** onboarding selectedModules | Webapp shell prioritises navigation order | apps/web routing |
| **Provides** onboarding frequencyPreset | Lane B's Soundscapes Home defaults to this preset | Lane B |
| **Provides** onboarding weeklyGoal | Lane A's Focus Hero Home shows progress vs goal | Lane A |
| **Coordinates** new auth.*/onboarding.* canonical events | Add to events file | Lane F |

## 10. Out of scope

- OAuth providers beyond Google + Apple (Phase 3).
- Username + password sign-in (deliberately omitted per ADR-0013).
- Native mobile sign-in (Phase 3 — Capacitor or RN handles via WebView).
- Account merging (a Supabase user signing in via passkey + email creates a single account, but cross-provider merging deferred).
- Real `services/rat-os-api` BFF — Phase 2.
- Sentry / observability — Phase 2 platform work.
- i18n marketing site copy — Phase 5.
- Anonymous-first sign-up (no signup needed for free tier) — rejected in ADR-0013.

## 11. Open questions / TODOs for implementation

| Question | Options | Recommended default | Decision owner |
|----------|---------|---------------------|-----------------|
| When the user signs up but doesn't complete onboarding, where do they land on next sign-in? | (a) `/onboarding` (resume) (b) `/focus` (skip) | (a) — soft-required, but Skip link available | Designer |
| Should the marketing site show a logged-in nav state? | (a) yes (b) no | (a) — `<HeaderUserChip />` when signed in; cleaner UX | Designer |
| Magic-link emails — branded or plaintext? | (a) HTML branded (b) plaintext | (a) Phase 1; document email template in provisioning runbook | Designer + Security |
| Passkey enrolment — required at signup or deferred? | (a) required (b) optional w/ deferral prompt | (b) — required friction is high; defer for users on devices that may not support |
| Onboarding Step 2 — skippable? | (a) yes (b) no | (a) — accessibility (some users can't hear binaural test); soundscapes default to Alpha | Designer |
| Right-to-Delete in Phase 1 with no BFF — manual operator process? | (a) yes (b) defer to Phase 2 | (a) — privacy commitment requires Phase 1 support even if manual | Security |
| Where do we store the tier cache TTL? | (a) magic number in tier.ts (b) env var | (a) — 60 s is the right value; document, don't configure |
| `G1.webapp-auth` row added in this lane's PR or in orchestrator follow-up? | (a) this PR (b) follow-up | (b) — same pattern as A8/B8/C7/D7 (orchestrator owns gate edits) | Coordinator |

---

> **When implementing**, the E5 hand-off signal is the most critical
> deliverable for cross-lane unblocking. Lane D's Wave-2 launch waits
> on `.agents/handoff/lane-e-e5.md` carrying the "E5 DONE" line. Write
> it explicitly; downstream tooling parses it.

> **See also:** ADR-0004, ADR-0013, PRD §1 / §2 / §7, PERSONAS.md, PRICING.md, `packages/adapters/identity-client/`, ROOT_AXIOMS PR-03, CONTEXT_SECURITY.md.
