import ast
from bs4 import BeautifulSoup
import esprima
import sass
from lxml import etree


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
        # Shut down some error types to be able to parse html from vue
        significant_errors = [
            error for error in parser.error_log
            if not error.message.startswith('Tag')
            and "error parsing attribute name" not in error.message
        ]
        if not significant_errors:
            return "Valid syntax"
        else:
            for error in significant_errors:
                return f"HTML line {error.line}: {error.message}"
    except etree.XMLSyntaxError as e:
        return f"Html error occurred: {e}"

def parse_javascript(js_content):
    try:
        esprima.parseScript(js_content)
        return "Valid syntax"
    except esprima.Error as e:
        return f"JavaScript syntax error: {e}"


def parse_scss(scss_code):
    try:
        sass.compile(string=scss_code)
        return "Valid syntax"
    except sass.CompileError as e:
       return f"CSS/SCSS syntax error: {e}"

def parse_vue(content):
    soup = BeautifulSoup(content, 'html.parser')

    # Extract and check HTML template
    template = soup.find('template')
    script = soup.find('script')
    style = soup.find('style')
    if template:
        parse_html(str(template))
    if script:
        parse_javascript(script.text)
    if style:
        parse_scss(style.text)


code = """
window.onload = function() {
    const image = document.getElementById('sourceImage');
    const canvas = document.getElementById('imageCanvas');
    const ctx = canvas.getContext('2d');

    image.onload = function() {
        // Set canvas size equal to image size
        canvas.width = image.width;
        canvas.height = image.height;

        // Draw the image onto the canvas
        ctx.drawImage(image, 0, 0);

        // Get the image data from the canvas
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;

        // Convert each pixel to grayscale
        for (let i = 0; i < data.length; i += 4) {
            const avg = (data[i] + data[i + 1] + data[i + 2]) / 3;
            data[i] = avg;     // Red
            data[i + 1] = avg; // Green
            data[i + 2] = avg; // Blue
        }

        // Put the modified data back to the canvas
        ctx.putImageData(imageData, 0, 0);
    };
};
"""

if __name__ == "__main__":
    parse_javascript(code)