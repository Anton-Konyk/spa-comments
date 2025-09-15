import vue from 'eslint-plugin-vue';
import prettier from 'eslint-plugin-prettier';
import vueParser from 'vue-eslint-parser';

export default [
  {
    files: ['**/*.vue', '**/*.js'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: '@babel/eslint-parser',
        requireConfigFile: false,
        ecmaVersion: 'latest',
        sourceType: 'module',
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    plugins: {
      vue,
      prettier,
    },
    rules: {
      'prettier/prettier': 'error',
      'vue/multi-word-component-names': 'off',
    },
  },
];
