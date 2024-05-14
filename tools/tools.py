from langchain.tools import tool
import os
import json
import base64
import playwright
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from bs4 import BeautifulSoup
import esprima
import sys
import subprocess

load_dotenv(find_dotenv())
work_dir = os.getenv("WORK_DIR")
OAIclient = OpenAI()


@tool
def list_dir(directory):
    """List files in directory.
    {"tool_input": {"directory": "Directory to check."}}
    """
    try:
        files = os.listdir(work_dir + directory)
        return files
    except Exception as e:
        return f"{type(e).__name__}: {e}"

@tool
def see_file(filename):
    """Check contents of file.
    {"tool_input": {"filename": "Name and path of file to check."}}
    """
    try:
        with open(work_dir + filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        formatted_lines = [f"<{i+1}>{line[:-1]}</{i+1}>\n" for i, line in enumerate(lines)]
        file_contents = "".join(formatted_lines)

        return file_contents
    except Exception as e:
        return f"{type(e).__name__}: {e}"


@tool
def see_image(filename):
    """Sees the image.
    {"tool_input": {"filename": "Name and path of image to check."}}
    """
    try:
        with open(work_dir + filename, 'rb') as image_file:
            img_encoded = base64.b64encode(image_file.read()).decode("utf-8")
        return img_encoded
    except Exception as e:
        return f"{type(e).__name__}: {e}"


def lint_code(code):
    """
    Lints the provided code using ESLint. Returns True if linting is successful, False otherwise.
    """
    try:
        # Write code to a temporary file
        with open('temp_code.js', 'w', encoding='utf-8') as file:
            file.write(code)

        # Run ESLint on the temporary file
        result = subprocess.run(['npx eslint', 'temp_code.js'], capture_output=True, text=True)
        if result.returncode == 0:
            return True
        else:
            print("Linting errors:", result.stdout)
            return False
    except Exception as e:
        print(f"Error during linting: {e}")
        return False


@tool
def insert_code(filename, line_number, code):
    """Insert new piece of code into provided file. Use when new code need to be added without replacing old one.
    Proper indentation is important.
    {"tool_input": {
        "filename": "Name and path of file to change.",
        "line_number": "Line number to insert new code after.",
        "code": "Code to insert in the file."
    }}
    """
    try:
        human_message = input("Write 'ok' if you agree with agent or provide commentary: ")
        if human_message != 'ok':
            return f"Action wasn't executed because of human interruption. He said: {human_message}"

        with open(work_dir + filename, 'r+', encoding='utf-8') as file:
            file_contents = file.readlines()
            file_contents.insert(line_number, code + '\n')
            file.seek(0)
            file.truncate()

            file.write("".join(file_contents))
        return "Code inserted"
    except Exception as e:
        return f"{type(e).__name__}: {e}"


@tool
def replace_code(filename, start_line, end_line, new_code):
    """Replace old piece of code between start_line and end_line with new one. Proper indentation is important.
    Do not use that function when want to insert new code without removing old one - use insert_code tool instead.
    Important: Pay extra attention to brackets when you are replacing an entire function or code block. Ensure that you
    include the closing bracket too in the 'end_line'. If you miss it, the program will not run correctly.
    {"tool_input": {
        "filename": "Name and path of file to change.",
        "start_line": "Start line number to replace with new code. Inclusive - means start_line will be first line to change.",
        "end_line": "End line number to replace with new code. Inclusive - means end_line will be last line to change.
        Be very vigilant about this - never forget to include the last line with the closing bracket while replacing
        an entire function or code block.",
        "new_code": "New piece of code to replace old one."
        }
    }
    """
    if not lint_code(new_code):
        return "Code has linting errors. Fix the errors and try again."

    try:
        human_message = input("Write 'ok' if you agree with agent or provide commentary: ")
        if human_message != 'ok':
            return f"Action wasn't executed because of human interruption. He said: {human_message}"

        with open(work_dir + filename, 'r+', encoding='utf-8') as file:
            file_contents = file.readlines()
            file_contents[start_line - 1:end_line] = [new_code + '\n']
            file.seek(0)
            file.truncate()
            file.write("".join(file_contents))
        return "Code modified"
    except Exception as e:
        return f"{type(e).__name__}: {e}"


@tool
def create_file_with_code(filename, code):
    """Create new file with provided code.
    :param filename: Name and path of file to create.
    :param code: Code to write in the file.
    """
    if not lint_code(code):
        return "Code has linting errors. Fix the errors and try again."

    try:
        human_message = input("Write 'ok' if you agree with agent or provide commentary: ")
        if human_message != 'ok':
            return f"Action wasn't executed because of human interruption. He said: {human_message}"

        with open(work_dir + filename, 'w', encoding='utf-8') as file:
            file.write(code)
        return "File been created successfully"
    except Exception as e:
        return f"{type(e).__name__}: {e}"


@tool
def image_to_code(prompt):
    """Writes a frontend code based on provided design with visual AI.
    :param prompt: Prompt to use for generation. Provide here that you want to receive code based on image, specify framework,
    any additional info if needed (as images to use).
    """
    try:
        with open(work_dir + "screenshots/template.png", "rb") as image_file:
            img_encoded = base64.b64encode(image_file.read()).decode("utf-8")
        response = OAIclient.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                      {"type": "text", "text": prompt},
                      {
                        "type": "image_url",
                        "image_url": {
                          "url": f"data:image/jpeg;base64,{img_encoded}",
                        },
                      },
                    ],
                }
            ],
            max_tokens=1000,
        )
        return lint_code(response.choices[0].message.content)
    except Exception as e:
        return f"{type(e).__name__}: {e}"


# function under development
def make_screenshot(endpoint, login_needed, commands):
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    if login_needed:
        page.goto('http://localhost:5555/login')
        page.fill('#username', 'uname')
        page.fill('#password', 'passwd')
        page.click('.login-form button[type="submit"]')
    page.goto(f'http://localhost:5555/{endpoint}')

    for command in commands:
        action = command.get('action')
        selector = command.get('selector')
        value = command.get('value')
        if action == 'fill':
            page.fill(selector, value)
        elif action == 'click':
            page.click(selector)
        elif action == 'hover':
            page.hover(selector)

    page.screenshot(path=work_dir + 'screenshots/screenshot.png')
    browser.close()


# @tool
# def parse_html(html_content):
#     try:
#         soup = BeautifulSoup(html_content, 'html.parser')
#         str(soup)  # This forces BS4 to parse and check for errors
#         print("HTML syntax appears to be valid.")
#     except Exception as e:
#         print(f"HTML syntax error: {e}")
#
#
# @tool
# def parse_javascript(js_content):
#     try:
#         esprima.parseScript(js_content)
#         print("JavaScript syntax appears to be valid.")
#     except esprima.Error as e:
#         print(f"JavaScript syntax error: {e}")
#
#
# @tool
# def check_vue_file(file_path):
#     with open(file_path, 'r', encoding='utf-8') as file:
#         content = file.read()
#
#     # Assuming standard .vue structure
#     soup = BeautifulSoup(content, 'html.parser')
#
#     # Extract and check HTML template
#     template = soup.find('template')
#     if template:
#         parse_html(str(template))
#
#     # Extract and check JavaScript
#     script = soup.find('script')
#     if script:
#         parse_javascript(script.text)
