import json
import re
import json5
import textwrap
import os

from termcolor import colored
from json import JSONDecodeError
from rich.panel import Panel
from rich.syntax import Syntax
from rich.console import Console
from rich.padding import Padding
from pygments.util import ClassNotFound
from pygments.lexers import get_lexer_by_name


def is_valid_path(path_str):
    # Check if the path format is valid
    try:
        path = os.path.normpath(path_str)
        return True
    except Exception:
        return False


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


def split_text_and_code(text):
    pattern = r'```(\w+)\s*\n(.*?)\n\s*```'
    parts = re.split(pattern, text, flags=re.DOTALL)
    result = []

    i = 0
    while i < len(parts):
        if i == 0 or i % 3 == 0:  # Text parts
            if parts[i].strip():
                result.append(('text', parts[i].strip()))
        else:  # Code block parts
            language = parts[i]
            content = parts[i + 1]
            result.append(('code', language, content.strip()))
            i += 1  # Skip the next part as we've already processed it
        i += 1

    return result


def process_text_content(text_content):
    if is_potential_json(text_content):
        # ta linijka się wywala, jeśli w tekscie są użyte nawiasy kwadratowe nie do jsona
        json_data = parse_json(text_content)

        if json_data and is_valid_tool_input(json_data):
            return process_tool_input(json_data['tool_input'])

    return [('text', text_content)]


def is_potential_json(text):
    return text.startswith(('{', '[')) and text.endswith(('}', ']'))


def parse_json(text):
    try:
        return json5.loads(text)
    except (JSONDecodeError, TypeError):
        return None


def is_valid_tool_input(json_data):
    return 'tool' in json_data and 'tool_input' in json_data


def process_tool_input(tool_input):
    if isinstance(tool_input, dict):
        code = tool_input.get('code')
        if code:
            return [create_code_tuple(tool_input)]
    return [('text', str(tool_input))]


def create_code_tuple(tool_input):
    code = tool_input['code']
    start_line = tool_input.get('start_line')
    line_number = tool_input.get('line_number')
    language = 'diff' if line_number is not None else tool_input.get('language', 'text')
    return 'code', language, code, start_line, line_number


def process_code_content(language, code_content):
    return 'code', language, code_content, None, None


def print_formatted_content(content):
    content_parts = split_text_and_code(content)

    for part in content_parts:
        if part[0] == 'text':
            print_comment(part[1])
        elif part[0] == 'code':
            language = part[1]
            code_content = part[2]
            json_data = extract_from_json(code_content)

            if not isinstance(json_data, dict):
                print_formatted_code(code=code_content, language=language, start_line=1, line_number=None)
                continue

            tool = json_data.get('tool')
            tool_input = json_data.get('tool_input', {})

            if isinstance(tool_input, str):
                print_tool_message(tool_name=tool, tool_input=tool_input, color="blue")

                if not is_valid_path(tool_input):
                    print_formatted_code(code=tool_input, language=language, start_line=1, line_number=None)
                continue

            code = tool_input.get('code')
            line_number = tool_input.get('line_number')
            start_line = tool_input.get('start_line')
            filename = tool_input.get('filename')

            if tool and code is None:
                print_tool_message(tool_name=tool, tool_input=tool_input or '', color="light_blue")
            elif code:
                if is_valid_path(filename):
                    print_tool_message(tool_name=tool, color="light_blue")
                print_formatted_code(code=code.strip(), language=language, start_line=start_line,
                                     line_number=line_number, title=filename)


def get_message_by_tool_name(tool_name):
    tool_messages = {
        "add_task": "It's time to add a new task:",
        "modify_task": "Let's modify the task:",
        "reorder_tasks": "Let's reorder tasks...",
        "create_epic": "Let's create an epic...",
        "modify_epic": "Let's modify the epic:",
        "finish_project_planning": "Project planning is finished",
        "list_dir": "Let's list files in a directory:",
        "see_file": "Looking at the file content...",
        "retrieve_files_by_semantic_query": "Let's find files by semantic query...",
        "insert_code": "Let's add some code...",
        "replace_code": "Some code needs to be updated...",
        "create_file_with_code": "Let's create a new file...",
        "ask_human_tool": "Ask human for input or actions.",
        "watch_web_page": "Visiting a web page...",
        "finish": "Hurray! The work is DONE!"
    }
    return f'\n{tool_messages.get(tool_name, "")}'


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


def safe_int(value):
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def print_formatted_code(code, language, start_line=1, line_number=None, title=''):
    console = Console()

    # Ensure start_line is an integer
    if not isinstance(start_line, int):
        start_line = 1

    # Ensure line_number is an integer if provided
    if line_number is not None and not isinstance(line_number, int):
        line_number = 1

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

            if len(snippet_title) > 100:
                snippet_title = 'Code Snippet'

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
            console.print("[bold red]Error: Code is None[/bold red]")


def print_error(message: str) -> None:
    print_formatted(content=message, color="red", bold=False)


def print_comment(message: str) -> None:
    print_formatted(content=message, color="dark_grey", bold=False, width=None)


def print_tool_message(tool_name, tool_input=None, color=None):
    message = get_message_by_tool_name(tool_name)

    if tool_input is None:
        print_formatted(content=message, color=color, bold=True)
    elif tool_name == 'ask_human':
        pass
    elif tool_name == 'final_response':
        json_string = json.dumps(tool_input, indent=2)
        print_formatted_code(code=json_string, language='json', title='Files:')
    elif tool_name in ['see_file', 'insert_code', 'create_file_with_code']:
        print_formatted(content=message, color=color, bold=True)
        print_formatted(content=tool_input, color='cyan', bold=True)
    elif tool_name == 'list_dir':
        print_formatted(content=message, color=color, bold=True)
        print_formatted(content=f'{tool_input}/', color='cyan', bold=True)
    elif tool_name == 'replace_code':
        message = f"Let's insert code on the place of lines {tool_input['start_line']} to {tool_input['end_line']}"
        print_formatted(content=message, color=color, bold=True)
        print_formatted(content=tool_input, color='yellow', bold=True)
    elif tool_name == 'finish':
        print_formatted(content=message, color='yellow', bold=True)
        print_formatted(content=tool_input, color=color, bold=True)
    elif tool_input and isinstance(tool_input, str) and tool_input.strip() != "":
        print_formatted(content=tool_input, color=color, bold=True)
    else:
        print_formatted(content=message, color=color, bold=True)
        print_formatted(content=tool_input, color=color, bold=True)


