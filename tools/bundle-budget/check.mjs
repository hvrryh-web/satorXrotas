#!/usr/bin/env node
/**
 * Bundle-budget validator.
 *
 * Reads tools/bundle-budget/budgets.json + the Vite/Next build report for
 * each app and emits a verdict for every route:
 *   - PASS (under soft limit)
 *   - WARN (between soft and hard limit)
 *   - FAIL (at or over hard limit)
 *
 * Exit code 0 on full PASS or WARN-only; 1 if any FAIL.
 *
 * Designed to run in two modes:
 *   1. `node tools/bundle-budget/check.mjs` — auto-discovers built artefacts
 *      under apps/site/.next, apps/web/dist
 *   2. `node tools/bundle-budget/check.mjs --report <path>` — explicit
 *      report file
 *
 * The size metric is gzipped chunk bytes. We approximate via gzip-size on
 * the underlying file when the build tool's report doesn't carry it.
 */

import { readFileSync, existsSync, statSync, readdirSync } from 'node:fs';
import { gzipSync } from 'node:zlib';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, '..', '..');

const budgetsPath = join(REPO_ROOT, 'tools', 'bundle-budget', 'budgets.json');
const budgets = JSON.parse(readFileSync(budgetsPath, 'utf8'));

const COLORS = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  green: '\x1b[32m',
  cyan: '\x1b[36m',
  dim: '\x1b[2m',
};

function color(c, s) {
  return process.stdout.isTTY ? `${COLORS[c]}${s}${COLORS.reset}` : s;
}

function humanBytes(n) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(2)} MB`;
}

function fileGzipSize(path) {
  const buf = readFileSync(path);
  return gzipSync(buf).length;
}

function discoverWebChunks() {
  const distDir =
    process.env.BUNDLE_BUDGET_WEB_DIST ??
    join(REPO_ROOT, 'apps', 'web', 'dist', 'assets');
  if (!existsSync(distDir)) return null;
  const files = readdirSync(distDir).filter(
    (f) => f.endsWith('.js') && !f.endsWith('.map')
  );
  if (files.length === 0) return null;
  const chunks = files.map((f) => {
    const full = join(distDir, f);
    const raw = statSync(full).size;
    const gz = fileGzipSize(full);
    return { file: f, rawBytes: raw, gzBytes: gz };
  });
  return chunks;
}

function discoverSiteChunks() {
  const distDir =
    process.env.BUNDLE_BUDGET_SITE_DIST ??
    join(REPO_ROOT, 'apps', 'site', '.next', 'static', 'chunks');
  if (!existsSync(distDir)) return null;
  const files = readdirSync(distDir).filter(
    (f) => f.endsWith('.js') && !f.endsWith('.map')
  );
  if (files.length === 0) return null;
  return files.map((f) => {
    const full = join(distDir, f);
    const raw = statSync(full).size;
    const gz = fileGzipSize(full);
    return { file: f, rawBytes: raw, gzBytes: gz };
  });
}

/**
 * Naive route-attribution heuristic. Vite emits one entry chunk + per-route
 * dynamic chunks named `<RouteName>-<hash>.js` when React.lazy is used.
 * Until React.lazy + suspense routes ship per-module, we attribute the
 * shell-total to `web://` (webapp shell) and per-module chunks (if any)
 * to their routes. Missing per-route chunks are reported as "not yet
 * code-split" but do not fail the budget.
 */
function attributeWebChunksToRoutes(chunks) {
  if (!chunks) return {};
  const attribution = {};
  const indexChunk = chunks.find((c) => /^index-/.test(c.file));
  if (indexChunk) {
    attribution['web://'] = indexChunk.gzBytes;
  } else {
    attribution['web://'] = chunks.reduce((acc, c) => acc + c.gzBytes, 0);
  }
  const moduleHints = {
    'web:/focus': /focus/i,
    'web:/sound': /sound/i,
    'web:/blocker': /blocker/i,
    'web:/write': /writ/i,
    'web:/learn': /learn/i,
    'web:/train': /train/i,
    'web:/world': /world/i,
  };
  for (const [route, re] of Object.entries(moduleHints)) {
    const chunk = chunks.find((c) => re.test(c.file));
    if (chunk) attribution[route] = chunk.gzBytes;
  }
  return attribution;
}

function attributeSiteChunksToRoutes(chunks) {
  if (!chunks) return {};
  const attribution = {};
  const total = chunks.reduce((acc, c) => acc + c.gzBytes, 0);
  attribution['site://'] = total;
  attribution['site:/modules'] = total;
  return attribution;
}

function verdict(route, measured, budget) {
  if (measured == null) return { state: 'SKIP', reason: 'no built artefact' };
  if (measured >= budget.hardLimit)
    return {
      state: 'FAIL',
      reason: `${humanBytes(measured)} ≥ hard limit ${humanBytes(budget.hardLimit)}`,
    };
  if (measured >= budget.softLimit)
    return {
      state: 'WARN',
      reason: `${humanBytes(measured)} between soft ${humanBytes(budget.softLimit)} and hard ${humanBytes(budget.hardLimit)}`,
    };
  return {
    state: 'PASS',
    reason: `${humanBytes(measured)} < soft ${humanBytes(budget.softLimit)}`,
  };
}

function main() {
  const webChunks = discoverWebChunks();
  const siteChunks = discoverSiteChunks();
  const measurements = {
    ...attributeWebChunksToRoutes(webChunks),
    ...attributeSiteChunksToRoutes(siteChunks),
  };

  const rows = [];
  let fails = 0;
  let warns = 0;
  let skips = 0;
  for (const [route, budget] of Object.entries(budgets.routes)) {
    const measured = measurements[route];
    const v = verdict(route, measured, budget);
    rows.push({ route, name: budget.name, measured, v });
    if (v.state === 'FAIL') fails += 1;
    else if (v.state === 'WARN') warns += 1;
    else if (v.state === 'SKIP') skips += 1;
  }

  console.log('\nBundle budget — measured first-paint chunks (gzipped)\n');
  console.log(
    '  STATUS  ROUTE                     NAME                          MEASURED'
  );
  console.log(
    '  ------  ------------------------  ----------------------------  ----------'
  );
  for (const { route, name, measured, v } of rows) {
    const stateColor =
      v.state === 'FAIL'
        ? 'red'
        : v.state === 'WARN'
          ? 'yellow'
          : v.state === 'PASS'
            ? 'green'
            : 'dim';
    const tag = color(stateColor, v.state.padEnd(6));
    const measuredStr = measured == null ? '—' : humanBytes(measured);
    console.log(
      `  ${tag}  ${route.padEnd(24)}  ${name.padEnd(28)}  ${measuredStr.padStart(10)}`
    );
    if (v.state !== 'PASS' && v.state !== 'SKIP') {
      console.log(`          ${color('dim', v.reason)}`);
    }
  }
  console.log('');
  console.log(
    `Summary: ${color('green', `${rows.length - fails - warns - skips} PASS`)}, ${color('yellow', `${warns} WARN`)}, ${color('red', `${fails} FAIL`)}, ${color('dim', `${skips} SKIP`)}`
  );

  if (fails > 0) {
    console.error(
      color('red', `\n✖ ${fails} route(s) exceed hard budget. Failing CI.`)
    );
    process.exit(1);
  }
  if (skips === rows.length) {
    console.error(
      color(
        'yellow',
        '\n⚠ No built artefacts found. Run `pnpm build` first; CI must run after the build step.'
      )
    );
    process.exit(1);
  }
  console.log(color('green', '\n✓ Bundle budgets respected.'));
}

main();
