# Security Policy

## Supported Versions

Pre-1.0: only the latest `main` is supported. Once we cut 1.0, we will support the latest minor + one prior.

## Reporting a Vulnerability

**Do not file public GitHub issues for security vulnerabilities.**

Email the maintainer at the address listed in `SUPPORT.md`. Include:

1. A description of the vulnerability and its impact.
2. Steps to reproduce (a minimal PoC if possible).
3. The version / commit SHA you tested against.
4. Your name + handle (so we can credit you in the advisory).

We aim to:

- Acknowledge receipt within **72 hours**.
- Confirm or deny the vulnerability within **7 days**.
- Ship a fix within **30 days** for high-severity issues.

## Scope

In scope:

- Code in this repository (`apps/`, `packages/`, `services/`, `contracts/`, `infra/`).
- The deployed marketing site and webapp.

Out of scope:

- Upstream `notbleaux/ZeSporteXte` services (file with that repo).
- Third-party dependencies (file with the upstream project).
- Social engineering of maintainers.
- Physical attacks against infrastructure.

## Disclosure

We follow coordinated disclosure. We will work with you on a fix, then publish a GitHub Security Advisory once the patch is available and users have had a reasonable window to update.

## Hall of Fame

Researchers who have responsibly disclosed vulnerabilities are credited here once their advisory is published.
