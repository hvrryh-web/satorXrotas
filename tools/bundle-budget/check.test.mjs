#!/usr/bin/env node
/**
 * Shell test for bundle-budget. Exercises three scenarios using an
 * isolated tmpdir so the test never touches real build artefacts.
 *
 * Run with `node tools/bundle-budget/check.test.mjs`.
 */

import { mkdirSync, writeFileSync, rmSync, mkdtempSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';
import { randomBytes } from 'node:crypto';
import { tmpdir } from 'node:os';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, '..', '..');
const CHECK = join(__dirname, 'check.mjs');

let passes = 0;
let fails = 0;

function logResult(name, ok, detail) {
  if (ok) {
    console.log(`  ✓ ${name}`);
    passes += 1;
  } else {
    console.error(`  ✗ ${name} — ${detail}`);
    fails += 1;
  }
}

function makeIsolatedDist() {
  return mkdtempSync(join(tmpdir(), 'bundle-budget-test-'));
}

function syntheticChunk(dir, name, gzTargetBytes) {
  mkdirSync(dir, { recursive: true });
  let payload = randomBytes(gzTargetBytes);
  while (gzipSync(payload).length < gzTargetBytes) {
    payload = Buffer.concat([payload, randomBytes(1024)]);
  }
  writeFileSync(join(dir, name), payload);
}

function runCheck(envOverrides = {}) {
  try {
    const out = execSync(`node ${CHECK}`, {
      cwd: REPO_ROOT,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: {
        ...process.env,
        NO_COLOR: '1',
        BUNDLE_BUDGET_WEB_DIST: envOverrides.web ?? '/nonexistent-web',
        BUNDLE_BUDGET_SITE_DIST: envOverrides.site ?? '/nonexistent-site',
      },
    });
    return { code: 0, stdout: out.toString(), stderr: '' };
  } catch (err) {
    return {
      code: err.status ?? 1,
      stdout: err.stdout?.toString() ?? '',
      stderr: err.stderr?.toString() ?? '',
    };
  }
}

const scenario1 = runCheck();
logResult(
  'scenario 1: no built artefacts → non-zero exit',
  scenario1.code !== 0 && scenario1.stderr.includes('No built artefacts'),
  `code=${scenario1.code} stderr=${scenario1.stderr.slice(0, 120)}`
);

const webDist2 = makeIsolatedDist();
syntheticChunk(webDist2, 'index-abc.js', 60_000);
syntheticChunk(webDist2, 'FocusRoute-def.js', 40_000);
const scenario2 = runCheck({ web: webDist2 });
rmSync(webDist2, { recursive: true, force: true });
logResult(
  'scenario 2: synthetic under-budget chunks → exit 0',
  scenario2.code === 0,
  `code=${scenario2.code} stderr=${scenario2.stderr.slice(0, 120)} stdout=${scenario2.stdout.slice(0, 200)}`
);

const webDist3 = makeIsolatedDist();
syntheticChunk(webDist3, 'index-abc.js', 200_000);
const scenario3 = runCheck({ web: webDist3 });
rmSync(webDist3, { recursive: true, force: true });
logResult(
  'scenario 3: synthetic over-hard-limit chunk → exit 1',
  scenario3.code === 1 && scenario3.stdout.includes('FAIL'),
  `code=${scenario3.code} stdout=${scenario3.stdout.slice(0, 200)}`
);

console.log('');
console.log(`bundle-budget check tests: ${passes} pass, ${fails} fail`);
if (fails > 0) process.exit(1);
