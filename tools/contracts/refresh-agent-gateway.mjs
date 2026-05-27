#!/usr/bin/env node
/**
 * Refresh contracts/openapi/agent-gateway.yaml against the latest
 * notbleaux/ZeSporteXte main SHA. Re-pins the upstream commit in the
 * canonical header.
 *
 * Per ADR-0014. Usage:
 *
 *   pnpm contracts:refresh-agent-gateway
 *
 * Exits 0 on no-change, 1 on diff (so CI can detect drift).
 */

import { writeFileSync, readFileSync, existsSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, '..', '..');
const TARGET = join(REPO_ROOT, 'contracts', 'openapi', 'agent-gateway.yaml');
const UPSTREAM_OWNER = 'notbleaux';
const UPSTREAM_REPO = 'ZeSporteXte';
const UPSTREAM_PATH = 'services/agent-gateway/openapi.json';

function authHeader() {
  const token = process.env.GITHUB_TOKEN ?? process.env.GH_TOKEN;
  return token ? `-H "Authorization: Bearer ${token}"` : '';
}

function fetchJson(url) {
  const out = execSync(`curl -fsSL ${authHeader()} "${url}"`, { encoding: 'utf8' });
  return JSON.parse(out);
}

function fetchText(url) {
  return execSync(`curl -fsSL ${authHeader()} "${url}"`, { encoding: 'utf8' });
}

function jsonToYaml(jsonText) {
  // Use python3 + PyYAML for deterministic block-style YAML.
  const py = `import json,yaml,sys
d=json.loads(sys.stdin.read())
print(yaml.dump(d,sort_keys=False,allow_unicode=True,default_flow_style=False,width=120),end='')`;
  return execSync(`python3 -c "${py.replace(/"/g, '\\"')}"`, {
    input: jsonText,
    encoding: 'utf8',
  });
}

function renderHeader(sha) {
  const today = new Date().toISOString().slice(0, 10);
  return [
    `# VENDORED — DO NOT HAND-EDIT.`,
    `# Source: ${UPSTREAM_OWNER}/${UPSTREAM_REPO}/${UPSTREAM_PATH}`,
    `# Pinned upstream SHA: ${sha}`,
    `# Pinned at: ${today} by refresh-agent-gateway.mjs`,
    `# Refresh via: pnpm contracts:refresh-agent-gateway`,
    `# Decision: ADR-0014 (Accepted) — Vendor agent-gateway openapi.json`,
    `# Consumer codegen wired behind G4.ai-personalization (Phase 4).`,
    ``,
    ``,
  ].join('\n');
}

function main() {
  console.warn(`Refreshing ${TARGET}`);

  const branchInfo = fetchJson(
    `https://api.github.com/repos/${UPSTREAM_OWNER}/${UPSTREAM_REPO}/commits/main`,
  );
  const sha = branchInfo.sha;
  console.warn(`Upstream main SHA: ${sha}`);

  const rawUrl = `https://raw.githubusercontent.com/${UPSTREAM_OWNER}/${UPSTREAM_REPO}/${sha}/${UPSTREAM_PATH}`;
  const jsonText = fetchText(rawUrl);
  const yamlBody = jsonToYaml(jsonText);

  const newContent = renderHeader(sha) + yamlBody;

  if (existsSync(TARGET)) {
    const oldContent = readFileSync(TARGET, 'utf8');
    if (oldContent === newContent) {
      console.warn('No change. Vendored file is up to date.');
      process.exit(0);
    }
  }

  writeFileSync(TARGET, newContent);
  console.warn(`Updated ${TARGET}`);
  console.warn(`Pinned at upstream SHA ${sha}.`);
  process.exit(1);
}

main();
