from langchain.tools import tool
import os
import json
import base64
import playwright
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from utilities.syntax_checker_functions import check_syntax


load_dotenv(find_dotenv())
work_dir = os.getenv("WORK_DIR")
OAIclient = OpenAI()

syntax_error_insert_code = """
Action is not executed, as it will cause next error: {error_response}. Probably you:
- Provided a wrong line number to insert code, or
- Forgot to add an indents on beginning of code.
Please analyze and rewrite your change proposition.
"""
syntax_error_modify_code = """
Action is not executed, as it will cause next error: {error_response}. Probably you:
- Provided a wrong end or beginning line number (end code line happens more often), or
- Forgot to add an indents on beginning of code.
Please analyze and rewrite your change proposition.
"""
@tool
def list_dir(directory):
    """List files in directory.
    tool input:
    :param directory: Name of directory to list files in.
    """
    try:
        files = os.listdir(work_dir + directory)
        return files
    except Exception as e:
        return f"{type(e).__name__}: {e}"


@tool
def see_file(filename):
    """Check contents of file.
    tool input:
    :param filename: Name and path of file to check.
    """
    try:
        with open(work_dir + filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        formatted_lines = [f"{i+1}|{line[:-1]}\n" for i, line in enumerate(lines)]
        file_content = "".join(formatted_lines)
        file_content = filename + ":\n\n" + file_content

        return file_content
    except Exception as e:
        return f"{type(e).__name__}: {e}"


@tool
def see_image(filename):
    """Sees the image.
    tool input:
    :param filename: Name and path of image to check.
    """
    try:
        with open(work_dir + filename, 'rb') as image_file:
            img_encoded = base64.b64encode(image_file.read()).decode("utf-8")
        return img_encoded
    except Exception as e:
        return f"{type(e).__name__}: {e}"


@tool
def insert_code(filename, line_number, code):
    """Insert new piece of code into provided file. Use when new code need to be added without replacing old one.
    Proper indentation is important.
    tool input:
    :param filename: Name and path of file to change.
    :param line_number: Line number to insert new code after.
    :param code: Code to insert into the file. Without backticks around. Start it with appropriate indentation if needed.
    """
    try:
        with open(work_dir + filename, 'r+', encoding='utf-8') as file:
            file_contents = file.readlines()
            file_contents.insert(line_number, code + '\n')
            file_contents = "".join(file_contents)
            check_syntax_response = check_syntax(file_contents, filename)
            if check_syntax_response != "Valid syntax":
                print("Wrong syntax provided, asking to correct.")
                return syntax_error_insert_code.format(error_response=check_syntax_response)
            human_message = input("Write 'ok' if you agree with agent or provide commentary: ")
            if human_message != 'ok':
                return f"Action wasn't executed because of human interruption. He said: {human_message}"
            file.seek(0)
            file.truncate()
            file.write(file_contents)
        return "Code inserted"
    except Exception as e:
        return f"{type(e).__name__}: {e}"


@tool
def replace_code(filename, start_line,  code, end_line):
    """Replace old piece of code between start_line and end_line with new one. Proper indentation is important.
    Do not use that function when want to insert new code without removing old one - use insert_code tool instead.
    tool input:
    :param filename: Name and path of file to change.
    :param start_line: Start line number to replace with new code. Inclusive - means start_line will be first line to change.
    :param code: New piece of code to replace old one. Without backticks around. Start it with appropriate indentation if needed.
    :param end_line: End line number to replace with new code. Inclusive - means end_line will be last line to change.
    """
    try:
        with open(work_dir + filename, 'r+', encoding='utf-8') as file:
            file_contents = file.readlines()
            file_contents[start_line - 1:end_line] = [code + '\n']
            file_contents = "".join(file_contents)
            check_syntax_response = check_syntax(file_contents, filename)
            if check_syntax_response != "Valid syntax":
                print("Wrong syntax provided, asking to correct.")
                return syntax_error_modify_code.format(error_response=check_syntax_response)
            human_message = input("Write 'ok' if you agree with agent or provide commentary: ")
            if human_message != 'ok':
                return f"Action wasn't executed because of human interruption. He said: {human_message}"
            file.seek(0)
            file.truncate()
            file.write(file_contents)
        return "Code modified"
    except Exception as e:
        return f"{type(e).__name__}: {e}"


@tool
def create_file_with_code(filename, code):
    """Create new file with provided code.
    tool input:
    :param filename: Name and path of file to create.
    :param code: Code to write in the file.
    """
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
def ask_human_tool(prompt):
    """
    Use that tool to ask human if you need any external information or actions.
    tool input:
    :param prompt: question to human.
    """
    try:
        human_message = input(prompt)
        return human_message
    except Exception as e:
        return f"{type(e).__name__}: {e}"

@tool
def image_to_code(prompt):
    """Writes a frontend code based on provided design with visual AI.
    <tool_input>
     <prompt>Prompt to use for generation. Provide here that you want to receive code based on image, specify framework,
     any additional info if needed (as images to use).</prompt>
    </tool_input>
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
        return response.choices[0].message.content
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
