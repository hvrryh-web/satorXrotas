# Engineering Standards

## Branching and Change Flow
- Use short-lived feature branches from `main`.
- Require pull requests for all production changes.
- Keep changes scoped to a single concern when possible.

## Code Review Standards
- At least one reviewer approval required.
- Validate architecture fit, security posture, and test quality.
- PRs must include user-facing impact and rollback notes.

## CI Baseline
- Run static checks, build, and tests on each PR.
- Block merges on failing checks.
- Publish build artifacts and test reports.

## Testing Baseline
- Unit tests for business logic and adapters.
- Integration tests for API + planner + AI adapter flow.
- End-to-end tests for critical onboarding and task workflows.

## Security Baseline
- No secrets committed to git.
- Dependency vulnerability scanning required on PR.
- Validate authz/authn paths and audit agent action logs.

## Release Flow
- Semver tags and changelog entries for releases.
- Staged promotion: dev -> staging -> production.
- Post-release health checks and rollback path documented.
