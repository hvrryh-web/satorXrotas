[Ver001.000]

# PR-03 — Trust & Privacy

## Default Stance

- **Local-first when possible.** Focus timer, soundscapes, writing drafts all work offline.
- **Server-required only when value justifies it** (social, cross-device sync, AI personalisation).
- **No third-party analytics in MVP.** All metrics flow through our own pipeline.
- **Opt-in for everything beyond core function.** Marketing emails, A/B groups, behavioural targeting — all explicit.

## Data Classification

| Tier | Examples | Storage |
|------|----------|---------|
| Public | Aggregate scores, leaderboards | Postgres, no encryption |
| User-private | Sessions, streaks, profile vector | Postgres, encrypted-at-rest |
| Sensitive | Manuscript text, journal entries, voice dictation transcripts | Encrypted-at-rest + per-user keys |
| Never collect | Browsing history outside our app, location, social graph | n/a |

## Retention

- Cognitive Profile: kept indefinitely while account active; deleted within 30 days of account deletion.
- Writing manuscripts: kept until user deletes; export available pre-delete.
- Soundscapes session events: 90 days of detail, then aggregated.
- Auth logs: 180 days.

## Right To Delete

User can delete account → all user-private + sensitive data wiped within 30 days. Aggregated, non-identifying analytics retained.

## Right To Export

User can export their own data → CSV/JSON bundle including sessions, streaks, profile, manuscripts, decks.

## What We Will Not Do

- Sell user data. Not to advertisers, not to "partners", not in an aggregated-but-reversible form.
- Train third-party models on user-private or sensitive data.
- Default to maximum data collection.
- Make deletion harder than signup.
