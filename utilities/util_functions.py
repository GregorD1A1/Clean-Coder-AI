import re
from json import JSONDecodeError

import json5
import os
import textwrap
import xml.etree.ElementTree as ET
import base64
import requests
from utilities.start_project_functions import file_folder_ignored, forbidden_files_and_folders

from dotenv import load_dotenv, find_dotenv
from pygments.util import ClassNotFound
from termcolor import colored
from todoist_api_python.api import TodoistAPI
from pygments.lexers import get_lexer_by_name
from rich.console import Console
from rich.syntax import Syntax
from rich.padding import Padding
from rich.panel import Panel

load_dotenv(find_dotenv())
work_dir = os.getenv("WORK_DIR")
log_file_path = os.getenv("LOG_FILE")
todoist_api = TodoistAPI(os.getenv('TODOIST_API_KEY'))
PROJECT_ID = os.getenv('TODOIST_PROJECT_ID')


def extract_from_json(content, parent_name=None, property_name=None):
    if not isinstance(content, (str, dict)):
        return content

    if isinstance(content, str):
        try:
            json_data = json5.loads(content)
        except (JSONDecodeError, ValueError):
            # If parsing fails, return the stripped content
            return content.strip()
    else:
        json_data = content

    if isinstance(json_data, dict):
        if parent_name and property_name:
            parent = json_data.get(parent_name, {})
            return parent.get(property_name) if isinstance(parent, dict) else None
        elif property_name:
            return json_data.get(property_name)
        elif parent_name:
            return json_data.get(parent_name)

    return json_data


# Helper function to check if content is valid JSON
def is_valid_json(content):
    try:
        json5.loads(content)
        return True
    except (JSONDecodeError, TypeError):
        return False


def process_code_block(code_block):
    # Regex pattern to match code blocks
    code_block_pattern = r'```(?:(\w+)\n)?(.*?)```'
    # Split the input string into parts based on the code block pattern
    parts = re.split(code_block_pattern, code_block, flags=re.DOTALL)
    result = []

    # Iterate over the parts and categorize them as text or code
    for i in range(0, len(parts), 3):
        if parts[i]:
            text = parts[i].strip()
            result.append(('text', text))
        if i + 2 < len(parts):
            language = parts[i + 1] if parts[i + 1] else None
            result.append(('code', language, parts[i + 2].strip()))

    return result


def extract_and_split_content(content):
    result = []

    for part in process_code_block(content):
        if part[0] == 'text':
            text_content = part[1]
            if text_content.startswith(('{', '[')) and text_content.endswith(('}', ']')):
                try:
                    json_data = json5.loads(text_content)
                    if 'tool' in json_data and 'tool_input' in json_data:
                        tool_input = json_data['tool_input']

                        if isinstance(tool_input, dict):
                            code = tool_input.get('code')
                            if code:
                                start_line = tool_input.get('start_line')
                                line_number = tool_input.get('line_number')

                                if line_number is not None:
                                    result.append(('code', 'diff', code, start_line, line_number))
                                else:
                                    language = tool_input.get('language', 'text')
                                    result.append(('code', language, code, start_line, line_number))
                            else:
                                result.append(('text', str(tool_input)))
                        else:
                            result.append(('text', str(tool_input)))
                        continue
                except (JSONDecodeError, TypeError):
                    pass
            result.append(('text', text_content))
        elif part[0] == 'code':
            language, code_content = part[1], part[2]
            result.append(('code', language, code_content, None, None))

    return result


def safe_int(value):
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def print_formatted_code(code, language, start_line=None, line_number=None, title=''):
    console = Console()

    # Ensure the language is set correctly for TypeScript
    language_tmp = 'typescript' if language in ['json5', 'typescript'] else language

    if code is None or (isinstance(code, str) and code.strip() == ""):
        console.print("[bold red]Error: No code to display[/bold red]")
        return

    start_line = safe_int(start_line) or safe_int(line_number)

    try:
        lexer = get_lexer_by_name(language_tmp or 'text')
    except ClassNotFound:
        lexer = get_lexer_by_name('text')

    try:
        if code:
            syntax = Syntax(
                code,
                lexer,
                line_numbers=True,
                start_line=start_line,
                theme="monokai",
                word_wrap=True,
                padding=(1, 1),
            )

            snippet_title = title or f"{language_tmp.capitalize() if isinstance(language_tmp, str) else 'Code'} Snippet"

            styled_code = Panel(
                syntax,
                border_style="bold yellow",
                title=snippet_title,
                expand=False
            )

            console.print(Padding(styled_code, 1))
        else:
            console.print("[bold red]Error: No code to display[/bold red]")
    except Exception as e:
        if code is not None:
            console.print("Fallback rendering:")
            syntax = Syntax(
                code,
                lexer,
                line_numbers=True,
                theme="monokai",
                word_wrap=True,
                padding=(1, 1),
            )

            snippet_title = title or f"{language_tmp.capitalize() if isinstance(language_tmp, str) else 'Code'} Snippet"

            styled_code = Panel(
                syntax,
                border_style="bold yellow",
                title=snippet_title,
                expand=False
            )

            console.print(Padding(styled_code, 1))
        else:
            console.print("[bold red]Error: Code is None[/bold red]")


def print_formatted_content(content):
    content_parts = extract_and_split_content(content)

    for part in content_parts:
        if part[0] == 'text':
            print_comment(part[1])
        elif part[0] in ['code', 'json']:
            tool = extract_from_json(part[2], parent_name='tool')
            input_text = extract_from_json(part[2], parent_name='tool_input')
            code = extract_from_json(part[2], parent_name='tool_input', property_name='code')
            line_number = extract_from_json(part[2], parent_name='tool_input', property_name='line_number')
            start_line = extract_from_json(part[2], parent_name='tool_input', property_name='start_line')

            if tool and not code:
                print_tool_message(tool_name=tool, tool_input=input_text or '', color="light_blue")
            elif isinstance(input_text, str):
                print_formatted_code(code=input_text, language=part[1], start_line=start_line, line_number=line_number)
            elif code:
                filename = extract_from_json(part[2], parent_name='tool_input', property_name='filename')
                filename = filename if filename else input_text
                language = part[1] if part[1] else 'text'
                print_formatted_code(code=code.strip(), language=language, start_line=start_line,
                                     line_number=line_number, title=filename)


def get_message_by_tool_name(tool_name, tool_input):
    if tool_name == 'create_file_with_code':
        return "Let's create a new file..."
    elif tool_name == 'see_file':
        return "Looking at the file content..."
    elif tool_name == 'list_dir':
        return "Let's list files in a directory:"
    elif tool_name == 'retrieve_files_by_semantic_query':
        return "Let's find files by semantic query..."
    elif tool_name == 'insert_code':
        return "Let's add some code..."
    elif tool_name == 'replace_code':
        return "Some code needs to be updated..."
    elif tool_name == 'add_task':
        return "It's time to add a new task:"
    elif tool_name == 'modify_task':
        return "Let's modify the task:"
    elif tool_name == 'reorder_tasks':
        return "Let's reorder tasks..."
    elif tool_name == 'create_epic':
        return "Let's create an epic..."
    elif tool_name == 'modify_epic':
        return "Let's modify the epic:"
    elif tool_name == 'finish_project_planning':
        return "Project planning is finished"

    return tool_input


def print_formatted(content, width=None, color=None, on_color=None, bold=False, end='\n'):
    if width:
        lines = content.split('\n')
        lines = [textwrap.fill(line, width=width) for line in lines]
        content = '\n'.join(lines)
    if bold:
        content = f"\033[1m{content}\033[0m"
    if color:
        content = colored(content, color, on_color=on_color, force_color=True)

    print(content, end=end)


def print_error(message: str) -> None:
    print_formatted(content=message, color="red", bold=False)


def print_comment(message: str) -> None:
    print_formatted(content=message, color="dark_grey", bold=False)


def print_tool_message(tool_name, tool_input=None, color=None):
    message = get_message_by_tool_name(tool_name, tool_input)

    print_formatted(content=message, color=color, bold=True)

    if tool_input:
        print_formatted(content=tool_input, color=color, bold=True)


def check_file_contents(files, work_dir):
    file_contents = str()
    for file_name in files:
        file_content = watch_file(file_name, work_dir)
        file_contents += file_content + "\n\n###\n\n"

    return file_contents


def watch_file(filename, work_dir):
    # if file_folder_ignored(filename, forbidden_files_and_folders):
    #    return "You are not allowed to work with this file."
    try:
        with open(join_paths(work_dir, filename), 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        return "File not exists."
    formatted_lines = [f"{i + 1}|{line[:-1]}\n" for i, line in enumerate(lines)]
    file_content = "".join(formatted_lines)
    file_content = filename + ":\n\n" + file_content

    return file_content


def find_tools_json(response):
    matches = re.findall(r'```(?:json|json5)\s*\n(.*?)\n\s*```', response, re.DOTALL)

    if not matches:
        return "No json found in response."

    results = []
    for match in matches:
        json_str = match.strip()
        try:
            json5_obj = json5.loads(json_str)
            results.append(json5_obj)
        except:
            results.append("Invalid json.")

    return results


def find_tool_xml(input_str):
    match = re.search('```xml(.*?)```', input_str, re.DOTALL)
    if match:
        root = ET.fromstring(match.group(1).strip())
        tool = root.find('tool').text.strip()
        tool_input_element = root.find('tool_input')
        tool_input = {}
        for child in tool_input_element:
            child.text = child.text.strip()
            if list(child):
                tool_input[child.tag] = [item.text for item in child]
            else:
                tool_input[child.tag] = child.text
        # output = {child.tag: child.text for child in root}
        return {"tool": tool, "tool_input": tool_input}
    else:
        return None


def check_application_logs():
    """Check out logs to see if application works correctly."""
    try:
        with open(log_file_path, 'r') as file:
            logs = file.read()
        if logs.strip().endswith("No messages found"):
            print("Logs are correct")
            return "Logs are correct"
        else:
            return logs
    except Exception as e:
        return f"{type(e).__name__}: {e}"


def see_image(filename, work_dir):
    try:
        with open(join_paths(work_dir, filename), 'rb') as image_file:
            img_encoded = base64.b64encode(image_file.read()).decode("utf-8")
        return img_encoded
    except Exception as e:
        return f"{type(e).__name__}: {e}"


def convert_images(image_paths):
    images = [
                 {"type": "text", "text": image_path}
                 for image_path in image_paths
             ] + [
                 {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{see_image(image_path, work_dir)}"}}
                 for image_path in image_paths
             ]
    # images for claude
    '''
    images.append(
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": see_image(image_path, work_dir),
            },
        }
    )
    '''
    return images


def join_paths(*args):
    leading_slash = '/' if args[0].startswith('/') else ''
    joined = leading_slash + '/'.join(p.strip('/') for p in args)
    return os.path.normpath(joined)


def get_joke():
    try:
        response = requests.get("https://v2.jokeapi.dev/joke/Programming?type=single")
        # response = requests.get("https://uselessfacts.jsph.pl//api/v2/facts/random")
        joke = response.json()["joke"] + "\n\n"
    except Exception as e:
        joke = f"Failed to receive joke :/"
    return joke


def list_directory_tree(work_dir):
    tree = []
    for root, dirs, files in os.walk(work_dir):
        # Filter out forbidden directories and files
        dirs[:] = [d for d in dirs if not file_folder_ignored(d, forbidden_files_and_folders)]
        files = [f for f in files if not file_folder_ignored(f, forbidden_files_and_folders)]

        rel_path = os.path.relpath(root, work_dir)
        if rel_path == '.':
            # This is the root directory, skip it
            continue

        depth = rel_path.count(os.sep)
        indent = "│   " * (depth - 1)

        # Add current directory to the tree
        tree.append(f"{indent}{'└──' if depth > 0 else ''}📁 {os.path.basename(root)}")

        # Add files to the tree
        file_indent = "│   " * depth + "├── "
        for i, file in enumerate(files):
            if i == len(files) - 1:
                file_indent = "│   " * depth + "└── "
            tree.append(f"{file_indent}{file}")

    return "Content of directory tree:\n" + "\n".join(tree)


def render_tools(tools) -> str:
    from inspect import signature
    descriptions = []
    for tool in tools:
        if hasattr(tool, "func") and tool.func:
            sig = signature(tool.func)
            description = f"tool_name: {tool.name}{sig}\n{tool.description}"
        else:
            description = f"{tool.name} - {tool.description}"

        descriptions.append(description)
    return "\n+++\n".join(descriptions)