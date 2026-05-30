#!/usr/bin/env node
/**
 * Shell test for tools/tokens-build/index.mjs.
 *   - Builds the tokens; asserts both generated files exist and are non-empty.
 *   - Runs `--check` mode; asserts exit 0 (clean state after build).
 *   - Mutates tokens.json transiently; runs `--check`; asserts non-zero.
 *   - Restores tokens.json.
 */

import { readFileSync, writeFileSync, existsSync, statSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, '..', '..');
const TOOL = join(__dirname, 'index.mjs');
const TOKENS = join(REPO_ROOT, 'packages', '@njz-os', 'ui', 'tokens', 'tokens.json');
const OUT_CSS = join(REPO_ROOT, 'packages', '@njz-os', 'ui', 'src', 'tokens', 'generated.css');
const OUT_TS = join(REPO_ROOT, 'packages', '@njz-os', 'ui', 'src', 'tokens', 'generated.ts');

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

function exec(cmd) {
  try {
    const out = execSync(cmd, { cwd: REPO_ROOT, stdio: ['ignore', 'pipe', 'pipe'] });
    return { code: 0, stdout: out.toString(), stderr: '' };
  } catch (err) {
    return {
      code: err.status ?? 1,
      stdout: err.stdout?.toString() ?? '',
      stderr: err.stderr?.toString() ?? '',
    };
  }
}

const buildResult = exec(`node ${TOOL}`);
logResult('build emits both files', buildResult.code === 0, buildResult.stderr);
logResult('generated.css exists + non-empty', existsSync(OUT_CSS) && statSync(OUT_CSS).size > 0, 'missing or empty');
logResult('generated.ts exists + non-empty', existsSync(OUT_TS) && statSync(OUT_TS).size > 0, 'missing or empty');

const checkClean = exec(`node ${TOOL} --check`);
logResult('--check returns 0 on clean state', checkClean.code === 0, `code=${checkClean.code} stderr=${checkClean.stderr.slice(0, 200)}`);

const originalTokens = readFileSync(TOKENS, 'utf8');
const mutated = originalTokens.replace('"#0F172A"', '"#000000"');
writeFileSync(TOKENS, mutated);
const checkDrift = exec(`node ${TOOL} --check`);
writeFileSync(TOKENS, originalTokens);
exec(`node ${TOOL}`);
logResult('--check returns non-zero on drift', checkDrift.code !== 0, `code=${checkDrift.code}`);

console.log('');
console.log(`tokens-build tests: ${passes} pass, ${fails} fail`);
if (fails > 0) process.exit(1);
