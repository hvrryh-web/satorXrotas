#!/usr/bin/env node
/**
 * Validate .doc-tiers.json — fail on:
 *  - manifest.approved_root_files lists a file that doesn't exist
 *  - a root-level .md file exists that's not in manifest.approved_root_files
 *  - T0 file doesn't exist
 *  - T1 path doesn't resolve to a file or directory
 *
 * Usage: node tools/doc-tier-check/index.mjs
 * Exit non-zero on failure.
 */

import { readFileSync, statSync, readdirSync } from 'node:fs';
import { join, resolve } from 'node:path';

const REPO = resolve(new URL('../..', import.meta.url).pathname);
const tiersFile = join(REPO, '.doc-tiers.json');

let failures = 0;

function fail(msg) {
  console.error('✗', msg);
  failures += 1;
}

function ok(msg) {
  console.log('✓', msg);
}

const tiers = JSON.parse(readFileSync(tiersFile, 'utf8'));

// 1. Approved root files exist
for (const f of tiers.manifest.approved_root_files) {
  try {
    statSync(join(REPO, f));
    ok(`root: ${f}`);
  } catch {
    fail(`root manifest lists missing file: ${f}`);
  }
}

// 2. No stray root .md files
const rootEntries = readdirSync(REPO);
const rootMd = rootEntries.filter((e) => e.endsWith('.md'));
for (const f of rootMd) {
  if (!tiers.manifest.approved_root_files.includes(f)) {
    fail(`root .md not in approved manifest: ${f}`);
  }
}

// 3. T0 files exist
for (const f of tiers.T0) {
  try {
    statSync(join(REPO, f));
  } catch {
    fail(`T0 missing: ${f}`);
  }
}

// 4. T1 paths resolve (file OR directory)
for (const f of tiers.T1) {
  try {
    statSync(join(REPO, f));
  } catch {
    fail(`T1 missing: ${f}`);
  }
}

if (failures > 0) {
  console.error(`\n${failures} doc-tier failure(s).`);
  process.exit(1);
} else {
  console.log('\nAll doc-tier checks passed.');
}
