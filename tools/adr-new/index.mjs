#!/usr/bin/env node
/**
 * Scaffold a new ADR.
 *
 * Usage: pnpm adr:new "Short title"
 *        → docs/architecture/ADR/ADR-XXXX-short-title.md
 */

import { readFileSync, readdirSync, writeFileSync, mkdirSync } from 'node:fs';
import { join, resolve } from 'node:path';

const REPO = resolve(new URL('../..', import.meta.url).pathname);
const ADR_DIR = join(REPO, 'docs/architecture/ADR');
const TEMPLATE = join(REPO, 'docs/governance/ADR_TEMPLATE.md');

const title = process.argv.slice(2).join(' ').trim();
if (!title) {
  console.error('Usage: pnpm adr:new "<Short title>"');
  process.exit(1);
}

mkdirSync(ADR_DIR, { recursive: true });

const existing = readdirSync(ADR_DIR)
  .filter((f) => /^ADR-\d{4}/.test(f))
  .map((f) => parseInt(f.slice(4, 8), 10))
  .filter((n) => !Number.isNaN(n));

const next = (existing.length ? Math.max(...existing) : 0) + 1;
const id = String(next).padStart(4, '0');
const slug = title
  .toLowerCase()
  .replace(/[^a-z0-9]+/g, '-')
  .replace(/^-|-$/g, '');
const filename = `ADR-${id}-${slug}.md`;
const filepath = join(ADR_DIR, filename);

let body = readFileSync(TEMPLATE, 'utf8');
body = body.replace('ADR-XXXX — <Short, descriptive title>', `ADR-${id} — ${title}`);
body = body.replace(/\*\*Date:\*\* YYYY-MM-DD/, `**Date:** ${new Date().toISOString().slice(0, 10)}`);

writeFileSync(filepath, body);
console.log(`Created ${filename}`);
console.log(`Status starts as Proposed. Flip to Accepted on CODEOWNER approval.`);
