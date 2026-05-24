[Ver001.000]

# STD-00 — Code Standards

## TypeScript

- `"strict": true`. Additionally enabled in `tsconfig.base.json`:
  - `noUnusedLocals`
  - `noUnusedParameters`
  - `noFallthroughCasesInSwitch`
  - `noUncheckedIndexedAccess`
  - `noImplicitOverride`
  - `verbatimModuleSyntax`

## Naming

| Kind | Convention | Example |
|------|------------|---------|
| Files | `kebab-case` | `focus-session.ts` |
| React components | `PascalCase` | `FocusTimer.tsx` |
| Hooks | `useCamelCase` | `useFocusSession` |
| Types / Interfaces | `PascalCase` | `FocusSession` |
| Type-only exports | suffix `-types.ts` for collections | `progression-types.ts` |
| Variables / functions | `camelCase` | `startSession()` |
| Constants | `SCREAMING_SNAKE` when truly constant | `DEFAULT_POMODORO_MIN = 25` |
| Enums | avoid; use string literal unions | `type Mode = 'pomodoro' \| 'deep_work'` |
| Brand types | `__camelCase` symbol property | `type UserId = string & { __userId: true }` |

## Imports

```ts
// 1. External packages
import { useState, type ReactNode } from 'react';
import { z } from 'zod';

// 2. Internal packages (@njz-os/*, @njz/*)
import { focusSessionSchema } from '@njz-os/focus-engine';

// 3. Local — absolute alias before relative
import { Button } from '@/components/Button';
import { formatDuration } from '../lib/time';
```

`type` keyword for type-only imports/exports always.

## React

- Functional components only. No class components.
- Server Components (Next.js) by default in `apps/site`; mark `'use client'` only when needed.
- Hooks: one custom hook per file. Compose, don't conflate.
- Props: prefer destructuring with defaults. Use `interface` for component props.
- Children: prefer composition over render props.

## Errors

- Throw `Error` subclasses with meaningful messages.
- Never `catch (e) { /* ignore */ }`. Either handle, rethrow, or log + re-throw.
- Adapter calls: always wrap with a typed retry/timeout, surface domain errors.

## Tests

- Vitest for unit + integration in packages.
- Playwright for E2E in apps.
- Coverage target: 80% on `@njz-os/*` packages, 60% on apps.
- Mock at the adapter boundary, not deeper.

## Formatting

- Prettier with config in `.prettierrc`. No exceptions.
- ESLint with config in `.eslintrc.cjs`. Warnings allowed, errors not.

## Comments

- Default: none. Code + good names should explain themselves.
- Only when WHY is non-obvious: hidden constraints, subtle invariants, workarounds for specific bugs.
- Never:
  - "This function does X" comments (the name should say so).
  - References to ticket numbers or PRs (rots fast; git blame is enough).
  - Commented-out code.

## TODOs

- Forbidden unless paired with an issue: `// TODO(#123): ...`.
- Or omit entirely and file the issue.
