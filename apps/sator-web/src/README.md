# apps/sator-web/src/

Placeholder for the SATOR public web platform.

## Purpose

The **SATOR web platform** is the online-facing component of the SATOR esports
simulation system. It displays public statistics (kills, deaths, assists, damage, etc.)
sourced exclusively from the `stats-schema` package — no game-internal data ever
reaches this layer.

## Planned Stack

- Framework: TBD (Next.js / SvelteKit)
- Data source: `/api` endpoints only
- Type safety: `packages/stats-schema` types imported directly

## Firewall Contract

This directory **must never** import from game source (`apps/radiantx-game`) directly.
All data arrives pre-sanitized through the API layer.

## Status

Phase 1 placeholder — implementation begins in Phase 3.
