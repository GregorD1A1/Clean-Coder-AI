import ast
from bs4 import BeautifulSoup
import esprima
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
        function_response = check_tag_balance(code, f'<{tag}', f'</{tag}>')
        if function_response != "Valid syntax":
            return function_response
    return "Valid syntax"


def parse_javascript(js_content):
    try:
        esprima.parseScript(js_content)
        return "Valid syntax"
    except esprima.Error as e:
        return f"JavaScript syntax error: {e}"


def check_tag_balance(code, open_tag, close_tag):
    opened_tags_count = 0
    open_tag_len = len(open_tag)
    close_tag_len = len(close_tag)

    i = 0
    while i < len(code):
        if code[i:i + open_tag_len] == open_tag:
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
        script = re.search(r'<script>(.*?)</script>', content, re.DOTALL).group(1)
    except AttributeError:
        return "Script part has no valid open/closing tags."
    script_part_response = check_tag_balance(script, "{", "}")
    if script_part_response != "Valid syntax":
        return script_part_response

    style_match = re.search(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
    if style_match:
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
<template>\n  <div class=\"profile-page-container\">\n    <div class=\"header\">\n      <span class=\"icon\">💼</span>\n      <div class=\"title
small-text\">Praca</div>\n    </div>\n    <div v-if=\"workData.photoUrl\" class=\"photo-frame\">\n      <img :src=\"apiUrl + workData.photoUrl.replace(/\\\\/g,
'/')\" alt=\"Work Photo\" class=\"photo-frame\"/>\n    </div>\n    <h2 class=\"big-text\">{{ workData.startYear }} - {{ workData.endYear }}</h2>\n    <p
class=\"small-text\">{{ workData.description }}</p>\n    <div class=\"location-arrow\">\n      <span class=\"icon\">👇</span>\n    </div>\n    <div
class=\"location-name small-text\">{{ workData.place }}</div>\n  </div>\n</template>\n\n<script>\nexport default {\n  name: 'WorkPage',\n  props: {\n
workData: {\n      type: Object,\n      required: true\n    }\n  },\n  data() {\n    return {\n      apiUrl: process.env.VUE_APP_API_URL\n    };\n
}\n};\n</script>\n\n<style lang=\"scss\" scoped>\n@import '@/assets/scss/MemorialProfile.scss';\n\n.profile-page-container {\n  background-image:
url('@/assets/images/profile_work_background.png');\n  padding-top: 8px; /* Reduced padding to decrease space at the top */\n}\n\n.header .icon {\n  font-size:
24px;\n}\n\n.title {\n  margin-top: 8px;\n  // Inherits small-text styles from profile.scss\n}\n\n.photo-frame {\n  margin-top: 16px;\n  border: 1px solid
#000;\n  height: 16rem; /* Further reduced height */\n  display: flex;\n  justify-content: center;\n  align-items: center;\n}\n\n\n.location-arrow .icon {\n
font-size: 24px; // Adjust size as needed\n  display: block; // Ensure the icon is centered\n  margin: 16px auto; // Center the icon horizontally and add some margin
\n}\n\n.location-name {\n  margin-top: 8px;\n  // Inherits small-text styles from profile.scss\n}\n\n/* Additional styles can be added as needed to match
the design */\n</style>
"""

if __name__ == "__main__":
    print(parse_vue_basic(code))
    pass