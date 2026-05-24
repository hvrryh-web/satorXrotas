// Root ESLint flat config (ESLint v9+).
// Single source of truth for the whole monorepo; per-package configs not needed
// unless a package wants explicit overrides.

import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default [
  {
    ignores: [
      '**/dist/**',
      '**/build/**',
      '**/.next/**',
      '**/.turbo/**',
      '**/node_modules/**',
      '**/coverage/**',
      '**/generated/**',
      '**/*.d.ts',
    ],
  },

  js.configs.recommended,
  ...tseslint.configs.recommended,

  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: {
        // Browser
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        fetch: 'readonly',
        AudioContext: 'readonly',
        AudioBuffer: 'readonly',
        OscillatorNode: 'readonly',
        Blob: 'readonly',
        URL: 'readonly',
        HTMLCanvasElement: 'readonly',
        HTMLAudioElement: 'readonly',
        // Node
        process: 'readonly',
        Buffer: 'readonly',
        __dirname: 'readonly',
        __filename: 'readonly',
        // Vite import.meta
        ImportMeta: 'readonly',
      },
    },
    rules: {
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
      '@typescript-eslint/consistent-type-imports': [
        'error',
        { prefer: 'type-imports' },
      ],
      'no-console': ['warn', { allow: ['warn', 'error'] }],
    },
  },

  // Loosen rules for tooling scripts (Node ESM, no TS)
  {
    files: ['tools/**/*.mjs', 'scripts/**/*.mjs', '*.config.{js,mjs,cjs,ts}'],
    rules: {
      'no-console': 'off',
    },
  },
];
