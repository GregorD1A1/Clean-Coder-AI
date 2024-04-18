from langchain.tools import tool
import os
import json
import base64
import playwright
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv


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
        human_message = input("Hit enter to allow that action:")
        if human_message:
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
    try:
        human_message = input("Hit enter to allow that action:")
        if human_message:
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
    try:
        human_message = input("Hit enter to allow that action:")
        if human_message:
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
        return response.choices[0].message.content
    except Exception as e:
        return f"{type(e).__name__}: {e}"


# funtion under development
def make_screenshot(endpoint, login_needed, commands):
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    if login_needed:
        page.goto('http://localhost:5555/login')
        page.fill('#username', 'juraj.kovac@op.pl')
        page.fill('#password', 'DnEcZTYB')
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

    page.screenshot(path='/home/autogen/autogen/takzyli-frontend/screenshots/screenshot.png')
    browser.close()

