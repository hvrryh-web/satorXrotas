/** ESLint preset for React packages and apps. */
const base = require('./index.cjs');

module.exports = {
  ...base,
  extends: [
    ...base.extends,
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:jsx-a11y/recommended',
  ],
  settings: {
    react: { version: 'detect' },
  },
  rules: {
    ...base.rules,
    'react/react-in-jsx-scope': 'off',
    'react/prop-types': 'off',
  },
};
