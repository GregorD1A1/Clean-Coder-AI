import ast
from bs4 import BeautifulSoup
import esprima


def check_syntax(file_content, filename):
    parts = filename.split(".")
    extension = parts[-1] if len(parts) > 1 else ''
    if extension == "py":
        return check_syntax_python(file_content)
    else:
        return "Valid syntax"


def check_syntax_python(code):
    try:
        ast.parse(code)
        return "Valid syntax"
    except SyntaxError as e:
        return f"Syntax Error: {e.msg} (line {e.lineno - 1})"
    except Exception as e:
        return f"Error: {e}"


def parse_html(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        str(soup)  # This forces BS4 to parse and check for errors
        print("HTML syntax appears to be valid.")
    except Exception as e:
        print(f"HTML syntax error: {e}")


def parse_javascript(js_content):
    try:
        esprima.parseScript(js_content)
        print("JavaScript syntax appears to be valid.")
    except esprima.Error as e:
        print(f"JavaScript syntax error: {e}")


def check_vue_file(content):
    # Assuming standard .vue structure
    soup = BeautifulSoup(content, 'html.parser')

    # Extract and check HTML template
    template = soup.find('template')
    if template:
        parse_html(str(template))

    # Extract and check JavaScript
    script = soup.find('script')

    if script:
        parse_javascript(script.text)
