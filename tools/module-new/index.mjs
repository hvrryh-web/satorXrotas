#!/usr/bin/env node
/**
 * Scaffold a new @njz-os/<name> package.
 *
 * Usage: pnpm module:new <name>
 *        → packages/@njz-os/<name>/{package.json,tsconfig.json,src/index.ts,README.md}
 */

import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

const REPO = resolve(new URL('../..', import.meta.url).pathname);

const name = process.argv[2];
if (!name || !/^[a-z][a-z0-9-]*$/.test(name)) {
  console.error('Usage: pnpm module:new <kebab-case-name>');
  process.exit(1);
}

const dir = join(REPO, 'packages/@njz-os', name);
if (existsSync(dir)) {
  console.error(`Package already exists: ${dir}`);
  process.exit(1);
}

mkdirSync(join(dir, 'src'), { recursive: true });

writeFileSync(
  join(dir, 'package.json'),
  `${JSON.stringify(
    {
      name: `@njz-os/${name}`,
      version: '0.0.0',
      private: true,
      type: 'module',
      description: `NJZ RAT-OS — ${name}`,
      main: './src/index.ts',
      types: './src/index.ts',
      scripts: {
        build: 'tsc',
        typecheck: 'tsc --noEmit',
        test: 'vitest run',
        lint: 'eslint src --max-warnings=0',
        clean: 'rm -rf dist .turbo',
      },
      dependencies: {
        '@njz-os/core': 'workspace:*',
      },
      devDependencies: {
        '@njz-os/tsconfig': 'workspace:*',
        typescript: '^5.6.0',
        vitest: '^2.0.0',
        eslint: '^9.0.0',
      },
    },
    null,
    2,
  )}\n`,
);

writeFileSync(
  join(dir, 'tsconfig.json'),
  `${JSON.stringify(
    {
      extends: '@njz-os/tsconfig/base.json',
      include: ['src/**/*'],
      exclude: ['node_modules', 'dist', '**/*.test.ts'],
    },
    null,
    2,
  )}\n`,
);

writeFileSync(
  join(dir, 'src/index.ts'),
  `export const VERSION = '0.0.0';\n`,
);

writeFileSync(
  join(dir, 'README.md'),
  `# @njz-os/${name}\n\nNJZ RAT-OS module — ${name}.\n\n## Next steps\n\n1. Add a prototype-system spec at docs/prototype-systems/PS-XXX-${name}.md\n2. Register types in .agents/SCHEMA_REGISTRY.md\n3. Update .agents/PHASE_GATES.md if gated\n`,
);

console.log(`Created @njz-os/${name}`);
console.log(`Don't forget:`);
console.log(`  - docs/prototype-systems/PS-XXX-${name}.md`);
console.log(`  - .agents/SCHEMA_REGISTRY.md`);
console.log(`  - .agents/PHASE_GATES.md (if gated)`);
