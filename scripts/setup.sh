#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v pnpm >/dev/null 2>&1; then
  echo "pnpm not found. Install: corepack enable && corepack prepare pnpm@9.12.0 --activate"
  exit 1
fi

echo "==> Installing workspace dependencies"
pnpm install --frozen-lockfile || pnpm install

if [ ! -f .env.local ]; then
  echo "==> Creating .env.local from .env.example"
  cp .env.example .env.local
fi

echo "==> Type-checking"
pnpm typecheck || echo "(typecheck failures — expected during Phase 0 if no deps installed yet)"

echo "==> Setup complete."
echo "Next: pnpm dev:site   (marketing site)"
echo "      pnpm dev:web    (webapp)"
