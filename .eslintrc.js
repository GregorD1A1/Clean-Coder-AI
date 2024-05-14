module.exports = {
    root: true,
    env: {
        node: true,
        browser: true,
    },
    extends: [
        'eslint:recommended',
        'plugin:vue/recommended',
        'prettier',
        'prettier/vue'
    ],
    parserOptions: {
        parser: 'babel-eslint', // or '@babel/eslint-parser'
        ecmaVersion: 2020,
        sourceType: 'module',
    },
    plugins: [
        'vue',
        'prettier'
    ],
    rules: {
        'prettier/prettier': 'error'
    }
};



