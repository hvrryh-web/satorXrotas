[Ver001.000]

# ADR-0013 — Auth Model (Passkeys + Email via Supabase Auth)

- **Status:** Accepted
- **Date:** 2026-05-24
- **Deciders:** @hvrryh-web
- **Tags:** auth, identity, passkeys, supabase, security
- **Protects gate:** Webapp shell + premium gate (G2.premium)

## Context

PRD §9 lists "Auth model: passkeys-only vs passkeys + email?" as a pre-Phase-1 open question. RAT-OS needs:

- A way to identify a user across devices (per cross-device sync requirement, PRD §2.1.2).
- A tier check (free / premium / team) gating ADR-0010 premium audio, ADR-0008's premium endpoints, and the eventual billing flow (Phase 2).
- An auth surface that the Distraction Blocker calendar OAuth (ADR-0011) can extend without re-architecting.
- A path to mobile native (Phase 3) that doesn't break the web session.

Constraints from ROOT_AXIOMS PR-03 (Trust & Privacy):

- Local-first when possible; server-required only when value justifies it.
- No third-party analytics in MVP — keeps the auth provider's tracking surface a real concern.
- Opt-in for everything beyond core function.

Upstream signal: `services/agent-gateway/supabase_mirror.py` already exists in `notbleaux/ZeSporteXte`. The platform team has chosen Supabase as the identity/data-mirror substrate for at least the agent surface. Aligning with this choice avoids splitting auth infrastructure between products.

## Decision

Use **Supabase Auth** as the identity provider, with **passkeys (WebAuthn) primary + email magic-link fallback**.

### Why Supabase Auth

- Already in use upstream (`supabase_mirror.py`); a shared identity substrate keeps a single user record across NJZ products.
- Free tier covers Phase 1 traffic comfortably (50,000 MAU on the free plan).
- Native WebAuthn / passkey support (no separate library required).
- HttpOnly cookie + refresh-token rotation handled by `@supabase/ssr` and `@supabase/auth-helpers`.
- Open-source server option available (`supabase/gotrue`) — escape hatch if the hosted SLA ever fails.

### Sign-in surface

| Method | When |
|--------|------|
| **Passkey** | Default for return visits on a device that has registered one. Triggered via `navigator.credentials.get` with `userVerification: "required"`. |
| **Email magic link** | First sign-up; sign-in on a fresh device that has no registered passkey; fallback if passkeys fail. |
| **OAuth (Google, Apple)** | Phase 2+. Added when the calendar-integration OAuth surface ships (ADR-0011) — Google's auth scope can carry the calendar read scope. |

No password flow. Passwords are deliberately omitted to avoid the credential-database liability.

### Session shape

- HttpOnly, `SameSite=Lax`, `Secure` cookie holds the Supabase refresh token.
- Access token (JWT) carried in memory by the SPA; refreshed automatically by `@supabase/ssr`.
- Session lifetime: 7 days; refresh extends. Long-term inactive sessions expire by Supabase default.
- `apps/site` reads the session cookie to render personalised marketing surfaces but never carries the JWT (server-rendered).
- `apps/web` reads the JWT via `@supabase/ssr` after hydration.

### CSRF

`SameSite=Lax` defends most cases. For state-changing requests, the SPA includes a **double-submit cookie token** (`X-NJZ-CSRF` header matching a cookie of the same name set on session start). Vaultbrain adapter validates the header on every mutation.

### Tier check (free / premium / team)

User's tier is stored in **vaultbrain** (per ADR-0008's `users` table, `tier` column) — *not* in the Supabase auth metadata. The auth JWT carries only identity; the tier is fetched via `GET /users/me` against vaultbrain (cached for 60 s in TanStack Query). This keeps the source of truth in our domain store, not in the auth provider.

### Sign-out

`POST /auth/v1/logout` to Supabase; cookie cleared; in-memory JWT discarded; TanStack Query cache evicted; redirect to `apps/site` root.

### Account deletion (Right to Delete — ROOT_AXIOMS PR-03)

`packages/adapters/identity-client/src/index.ts` exposes `deleteAccount()` which:

1. Calls `services/rat-os-api/users/me` `DELETE` (Phase 2 — `rat-os-api` is the BFF for this since it must orchestrate vaultbrain + Supabase deletion atomically).
2. BFF deletes the vaultbrain user row and all owned rows; queues Supabase user deletion via `auth.admin.deleteUser()`.
3. Within 30 days per PR-03, all user-private and sensitive data is wiped.

### Passkey enrolment

On first sign-up via email magic link, the webapp immediately prompts the user to enroll a passkey (deferrable but encouraged). Subsequent devices can enrol a passkey from the account settings page. Supabase Auth issues credentials bound to `rpId` of the production domain; preview deploys use a separate Supabase project to avoid polluting prod credentials.

### Native shells (Phase 3)

Capacitor or React Native (decision deferred to its own ADR) wrap `apps/web`. Supabase Auth supports both; passkeys work via the OS-native API (iOS keychain, Android Credential Manager). Same Supabase project; same cookie/JWT semantics through the WebView. Native-specific token storage uses `@capacitor/preferences` or RN's secure store.

### What Supabase does NOT own

- The cognitive profile, focus sessions, streaks, progression events — all live in vaultbrain per ADR-0008.
- Soundscape favourites, manuscript metadata, deck progress — all vaultbrain.
- Billing — Phase 2; provider TBD (Stripe likely). Billing is a separate ADR; tier mutations flow through the BFF.

## Consequences

**Positive:**

- Single auth surface across NJZ products (RAT-OS + eSports + future).
- Passkey-primary defeats phishing and credential stuffing — the two largest auth attack classes.
- No password database to breach or rotate.
- Free Supabase tier covers Phase 1; predictable cost growth (paid tier = $25/mo for 100K MAU when needed).
- Account deletion path is explicit and atomic via the BFF.

**Negative:**

- Hard dependency on Supabase availability. Mitigation: the open-source `gotrue` is forkable if hosted Supabase ever fails us; vaultbrain's user table is our source of identity-truth, not Supabase's auth table.
- Passkey UX is improving but still confuses first-time users. Mitigation: clear marketing copy ("Sign in with your face — no password ever") and the email fallback.
- Some users won't have a passkey-capable device. Email magic link covers them.
- Supabase has its own analytics/telemetry; we disable what we can, accept the rest, and document it in `SECURITY.md`.

**Neutral:**

- Webapp loads `@supabase/ssr` (~30 KB gzipped). Acceptable.
- The session-cookie boundary is the same domain for `apps/site` and `apps/web`; this requires same-domain hosting per ADR-0004 (already chosen).

## Alternatives Considered

- **Self-hosted Auth.js / NextAuth.** Rejected: more infra to run; we'd build the WebAuthn flow ourselves; doesn't share identity with upstream.
- **Clerk / Auth0 / WorkOS.** Rejected: cost (~$25–$150/mo even at Phase 1 scale); does not align with upstream's Supabase choice.
- **Firebase Auth.** Rejected: Google dependency; conflicts with the open-source-first axiom; less control.
- **Roll our own passkey server.** Rejected: cryptographically demanding; one bug = a credential-database breach. Use the audited Supabase implementation.
- **Passwords + magic-link only (skip passkeys).** Rejected: misses the modern security baseline; passkey-primary is a measurable trust signal for the target personas.
- **Anonymous-first (no signup for free tier).** Rejected: cross-device sync (a core PRD promise) requires identity; anonymous accounts also lose data when the user changes devices.

## Related

- ADR-0008 — Vaultbrain integration shape (`users` table; tier source-of-truth lives there).
- ADR-0011 — Distraction Blocker (calendar OAuth integrates here in Phase 2).
- `docs/product/PRD.md` §9 — Auth open question, now answered.
- `packages/adapters/identity-client/README.md` — wraps Supabase calls; stub now, real impl in Phase 1.
- `services/rat-os-api/` — orchestrates atomic deletion across Supabase + vaultbrain (Phase 2).
- Upstream reference: `services/agent-gateway/supabase_mirror.py`.

---

> When proposing, leave Status: Proposed. On approval, change to Accepted in a follow-up commit.
> Append a one-line entry to `.agents/DECISION_LOG.md` referencing this ADR.
