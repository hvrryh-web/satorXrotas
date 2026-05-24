#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> doc-tier:check"
node tools/doc-tier-check/index.mjs

echo "==> typecheck"
pnpm typecheck

echo "==> lint"
pnpm lint

echo "==> test"
pnpm test

echo "==> all checks passed"
