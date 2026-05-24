[Ver001.000]

# PR-01 — Engineering Ethos

## Core Beliefs

1. **Zero-budget, open-source first.** Every dependency is open-source, community-maintained, production-proven. No paid services in the critical path of MVP.
2. **Boring tech where possible.** TypeScript, React, Postgres, Redis — not because they're exciting but because hiring, hiring AIs, and shipping all win on a boring base.
3. **Domain types over framework cleverness.** Model the cognitive states (focus session, streak, profile vector) cleanly; the framework is interchangeable.
4. **One contract, two surfaces.** The site and the webapp share types. They do not share runtimes or routing. They share *meaning*.
5. **Small, frequent commits.** A coherent change is one commit, even if it's a 600-line refactor. A grab-bag is many commits.
6. **Reversibility over speed.** Prefer a slower change that's easy to undo to a fast one that's hard to undo.

## Tactical Rules

- TypeScript strict. `noUnusedLocals`, `noUnusedParameters`, `noUncheckedIndexedAccess` all on.
- Imports: `type` keyword for type-only.
- Errors: throw `Error` subclasses with meaningful messages. Never silently swallow.
- Async: prefer `Promise.all` over sequential `await`s when independent.
- Side effects: at module boundaries only. Pure functions everywhere else.
- Files: one responsibility per file. Don't fear creating a new file; do fear a file becoming a junk drawer.

## Anti-Patterns We Reject

- Adding a v2 file alongside a v1. Just edit v1.
- "Wrapper" classes around third-party libraries that add no value.
- Sprinkling `try { ... } catch { /* ignore */ }` blocks.
- Premature performance optimisation (measure first).
- Mocking everything in tests. Test real behaviour where reasonable.

## When You Don't Know What's Right

- Default to the simpler option.
- If you must choose between elegance and clarity, pick clarity.
- If you must choose between flexibility and locality, pick locality.
- Three similar lines are better than one premature abstraction.
