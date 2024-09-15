import ast
from bs4 import BeautifulSoup
import esprima
import pyjsparser
import sass
from lxml import etree
import re


def check_syntax(file_content, filename):
    parts = filename.split(".")
    extension = parts[-1] if len(parts) > 1 else ''
    if extension == "py":
        return parse_python(file_content)
    elif extension in ["html", "htm"]:
        return parse_html(file_content)
    elif extension == "js":
        return parse_javascript(file_content)
    elif extension in ["css", "scss"]:
        return parse_scss(file_content)
    elif extension == "vue":
        return parse_vue_basic(file_content)
    else:
        return "Valid syntax"


def parse_python(code):
    try:
        ast.parse(code)
        return "Valid syntax"
    except SyntaxError as e:
        return f"Syntax Error: {e.msg} (line {e.lineno - 1})"
    except Exception as e:
        return f"Error: {e}"


def parse_html(html_content):
    parser = etree.HTMLParser(recover=True)  # Enable recovery mode
    try:
        html_tree = etree.fromstring(html_content, parser)
        significant_errors = [
            error for error in parser.error_log
            # Shut down some error types to be able to parse html from vue
            #if not error.message.startswith('Tag')
            #and "error parsing attribute name" not in error.message
        ]
        if not significant_errors:
            return "Valid syntax"
        else:
            for error in significant_errors:
                return f"HTML line {error.line}: {error.message}"
    except etree.XMLSyntaxError as e:
        return f"Html error occurred: {e}"


def parse_vue_template_part(code):
    for tag in ['div', 'p', 'span']:
        function_response = check_template_tag_balance(code, f'<{tag}', f'</{tag}>')
        if function_response != "Valid syntax":
            return function_response
    return "Valid syntax"


def parse_javascript(js_content):
    try:
        esprima.parseModule(js_content)
        return "Valid syntax"
    except esprima.Error as e:
        print(f"Esprima syntax error: {e}")
        return f"JavaScript syntax error: {e}"


def check_template_tag_balance(code, open_tag, close_tag):
    opened_tags_count = 0
    open_tag_len = len(open_tag)
    close_tag_len = len(close_tag)

    i = 0
    while i < len(code):
        # check for open tag plus '>' or space after
        if code[i:i + open_tag_len] == open_tag and code[i + open_tag_len] in [' ', '>', '\n']:
            opened_tags_count += 1
            i += open_tag_len
        elif code[i:i + close_tag_len] == close_tag:
            opened_tags_count -= 1
            i += close_tag_len
            if opened_tags_count < 0:
                return f"Invalid syntax, mismatch of {open_tag} and {close_tag}"
        else:
            i += 1

    if opened_tags_count == 0:
        return "Valid syntax"
    else:
        return f"Invalid syntax, mismatch of {open_tag} and {close_tag}"


def check_bracket_balance(code):
    opened_brackets_count = 0

    for char in code:
        if char == '{':
            opened_brackets_count += 1
        elif char == '}':
            opened_brackets_count -= 1
            if opened_brackets_count < 0:
                return "Invalid syntax, mismatch of { and }"

    if opened_brackets_count == 0:
        return "Valid syntax"
    else:
        return "Invalid syntax, mismatch of { and }"


def parse_scss(scss_code):
    # removing import statements as they cousing error, because function has no access to filesystem
    scss_code = re.sub(r'@import\s+[\'"].*?[\'"];', '', scss_code)
    try:
        sass.compile(string=scss_code)
        return "Valid syntax"
    except sass.CompileError as e:
       return f"CSS/SCSS syntax error: {e}"


# That function does not guarantee finding all the syntax errors in template and script part; but mostly works
def parse_vue_basic(content):
    start_tag_template = re.search(r'<template>', content).end()
    end_tag_template = content.rindex('</template>')
    template = content[start_tag_template:end_tag_template]
    template_part_response = parse_vue_template_part(template)
    if template_part_response != "Valid syntax":
        return template_part_response

    try:
        script = re.search(r'<script[^>]*>(.*?)</script>', content, re.DOTALL).group(1)
    except AttributeError:
        return "Script part has no valid open/closing tags."
    script_part_response = check_bracket_balance(script)
    if script_part_response != "Valid syntax":
        return script_part_response

    style_match = re.search(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
    if style_match:
        css = style_match.group(1)
        if css:     # if for the case of empty css block
            style_part_response = parse_scss(style_match.group(1))
            if style_part_response != "Valid syntax":
                return style_part_response

    return "Valid syntax"

# Function under development
def lint_vue_code(code_string):
    import subprocess
    import os
    eslint_config_path = '.eslintrc.js'
    temp_file_path = "dzik.vue"
    # Create a temporary file
    with open(temp_file_path, 'w', encoding='utf-8') as file:
        file.write(code_string)
    try:
        # Run ESLint on the temporary file
        result = subprocess.run(['D:\\NodeJS\\npx.cmd', 'eslint', '--config', eslint_config_path, temp_file_path, '--fix'], check=True, text=True, capture_output=True)
        print("Linting successful:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error during linting:", e.stderr)
    finally:
        # Clean up by deleting the temporary file
        os.remove(temp_file_path)



code = """
// /utils/logger.js
const axios = require('axios');
axios.defaults.baseURL = process.env.VUE_APP_DEV_SERVER_API_URL;

const endpointName = '/logs/frontend-errors';

const formatErrorMessage = (error, type = 'error') => {
    const baseMessage = error && error.message
      ? JSON.stringify(error.message.replace(/\n/g, ''))
        .replace(/\\u00[\da-zA-Z]{2}\[\d+m/g, '')
        .replace(/\s{2,}/g, ' ')
      : 'No messages found';
    return type === 'warning' ? `Warning: ${baseMessage}` : baseMessage;
}

const sendLogErrorRequest = (message) => {
    axios.post(endpointName, { message })
        .then(() => {
            console.log(`Successful logged to file`);
        })
        .catch(error => {
            console.error('Log to file failed: ', error);
        });
}

const getFormattedErrorMessages = (error, message) => {
    // eslint-disable-next-line no-control-regex
    const cleanOutput = message.replace(/\u001b\[[0-9;]*m/g, '');
    // Split by a pattern that matches the common part of the file paths
    const errorsByFile = cleanOutput.split(/(?=Takzyli-frontend\/src\/)/);
    // Filter out empty strings and the initial part if it doesn't contain file errors
    const filteredErrors = errorsByFile.filter(e => e && !e.startsWith('[eslint]'));
    // Combine errors for each file
    const formattedErrors = filteredErrors.map(fileErrors => {
        return fileErrors.trim().replace(/\n+/g, ' ').replace(/\s+/g, ' ');
    });
    const errorMessages = formattedErrors.filter(message => message.includes('error'));
    const cleanedMessages = [...errorMessages]
        .map(errorMessage => errorMessage
            .replace(/ error /g,' ')
            .replace(/✖ .*/g, '')
        );

    const transformedErrors = cleanedMessages.flatMap((item) => {
        // Remove any trailing path segment that appears at the end of an item
        const cleanedItem = item.replace(/\/[A-Za-z/_-]+\/$/, '');
        // Extract the file path and errors from each cleaned item
        const [filePath, ...errors] = cleanedItem.split(/ (?=\d+:\d+)/);
        // Prepend the file path to each error and return the new array of errors
        return errors.map(error => `${filePath} ${error}`);
    })

    return transformedErrors.sort((a, b) => {
        // Extract file paths from the error strings
        const filePathA = a.split(' ')[0];
        const filePathB = b.split(' ')[0];

        // Compare file paths to sort
        return filePathA.localeCompare(filePathB);
    });
}

const logErrorToServer = (error, type = 'error') => {
    const errorMessage = formatErrorMessage(error, type);
    const errorName = error ? error.name : null;

    if (error) {
        const errorMessagesSortedByPath = getFormattedErrorMessages(error, errorMessage);

        errorMessagesSortedByPath.forEach((message) => {
            const errorMessage = `
                ${new Date().toISOString() + ' | '}
                ${errorName ? errorName + ' | ' : ''}
                ${message || 'No errors found'}
           `.trim();

            const formattedMessage = errorMessage.split('\n').map(item => item.trim()).join(' ');

            sendLogErrorRequest(formattedMessage);
        });
    } else {
        const formattedMessage = `
            ${new Date().toISOString() + ' | '}
            ${errorMessage}
       `.replace(/\s{2,}/g, ' ').trim();

        sendLogErrorRequest(formattedMessage);
    }
}

const clearFrontendLogs = () => {
    axios.delete(endpointName)
        .then(() => {
            console.log('Frontend logs cleared successfully');
        })
        .catch(error => {
            console.error('Frontend logs clearing failed:', error);
        });
}

module.exports = { logErrorToServer, clearFrontendLogs };

"""

if __name__ == "__main__":
    pyjsparser.parse(code)