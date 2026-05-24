# NJZ RAT-OS — Windows setup
$ErrorActionPreference = 'Stop'

Set-Location (Join-Path $PSScriptRoot '..')

if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
  Write-Error "pnpm not found. Install: 'corepack enable; corepack prepare pnpm@9.12.0 --activate'"
  exit 1
}

Write-Host '==> Installing workspace dependencies' -ForegroundColor Cyan
pnpm install --frozen-lockfile
if ($LASTEXITCODE -ne 0) { pnpm install }

if (-not (Test-Path .env.local)) {
  Write-Host '==> Creating .env.local from .env.example' -ForegroundColor Cyan
  Copy-Item .env.example .env.local
}

Write-Host '==> Type-checking' -ForegroundColor Cyan
pnpm typecheck

Write-Host '==> Setup complete.' -ForegroundColor Green
Write-Host 'Next: pnpm dev:site (marketing) | pnpm dev:web (webapp)'
