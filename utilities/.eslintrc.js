// eslint-disable-next-line no-undef
module.exports = {
    parserOptions: {
        ecmaVersion: 2020, // You can set this to 2015 or later
        sourceType: 'module', // Indicates that you're using ES6 modules
        ecmaFeatures: {
            jsx: true, // Enable parsing of JSX
        },
    },
    globals: {
        image: "readonly", // This tells ESLint that `image` is a global variable that should not be re-assigned
    },
    env: {
        node: true  // This line indicates that the code is expected to run in a Node.js environment
    },
    extends: [
        "eslint:recommended",          // Enables a set of core rules recommended by ESLint
        "plugin:vue/vue3-recommended"  // Enables a set of rules recommended for Vue 3 projects
    ],
    rules: {
        "no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],  // Configures the no-unused-vars rule
        "no-undef": ["error"],
        "vue/no-unused-vars": "error",
        "vue/max-attributes-per-line": "off",
        "vue/attributes-order": "off",
        "vue/singleline-html-element-content-newline": "off",
        "vue/html-indent": "off",
        "vue/html-self-closing": "off",
        "vue/multiline-html-element-content-newline": "off",
        "vue/html-closing-bracket-spacing": "off",
        "vue/multi-word-component-names": "off",
    }
};
