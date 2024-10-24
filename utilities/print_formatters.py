import re
import json5
import textwrap

from termcolor import colored
from itertools import zip_longest
from json import JSONDecodeError
from rich.panel import Panel
from rich.syntax import Syntax
from rich.console import Console
from rich.padding import Padding
from pygments.util import ClassNotFound
from pygments.lexers import get_lexer_by_name


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


def extract_code_blocks(text):
    """
    Extract code blocks from the given text.

    Args:
        text (str): The input text containing code blocks.

    Returns:
        list: A list of tuples containing (language, code) for each code block.
    """
    code_block_pattern = r'```(?:(\w+)\n)?(.*?)```'
    matches = re.findall(code_block_pattern, text, flags=re.DOTALL)
    return [(lang or None, code.strip()) for lang, code in matches]


def split_text_and_code(text):
    """
    Split the input text into text and code parts.

    Args:
        text (str): The input text containing code blocks.

    Returns:
        list: A list of tuples containing ('text', content) or ('code', language, content).
    """
    code_block_pattern = r'```(?:\w+\n)?.*?```'
    parts = re.split(code_block_pattern, text, flags=re.DOTALL)
    text_parts = [part.strip() for part in parts if part.strip()]

    code_blocks = extract_code_blocks(text)

    result = []
    for text_part, code_block in zip_longest(text_parts, code_blocks, fillvalue=None):
        if text_part:
            result.append(('text', text_part))
        if code_block:
            result.append(('code', *code_block))

    return result


def extract_and_split_content(content):
    result = []
    for part in split_text_and_code(content):
        if part[0] == 'text':
            result.extend(process_text_content(part[1]))
        elif part[0] == 'code':
            result.append(process_code_content(*part[1:]))
    return result


def process_text_content(text_content):
    if is_potential_json(text_content):
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


def print_error(message: str) -> None:
    print_formatted(content=message, color="red", bold=False)


def print_comment(message: str) -> None:
    print_formatted(content=message, color="dark_grey", bold=False)


def print_tool_message(tool_name, tool_input=None, color=None):
    message = get_message_by_tool_name(tool_name, tool_input)

    print_formatted(content=message, color=color, bold=True)

    if tool_input:
        print_formatted(content=tool_input, color=color, bold=True)
