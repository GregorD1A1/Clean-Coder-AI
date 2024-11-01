import json
import re
import json5
import textwrap
from termcolor import colored
from json import JSONDecodeError
from rich.panel import Panel
from rich.syntax import Syntax
from rich.console import Console
from rich.padding import Padding
from pygments.util import ClassNotFound
from pygments.lexers import get_lexer_by_name


def split_text_and_code(text):
    pattern = r'```(\w+)\s*\n(.*?)\n\s*```'
    parts = re.split(pattern, text, flags=re.DOTALL)
    result = []
    for i, part in enumerate(parts):
        if i == 0 or i % 3 == 0:  # Text parts
            if parts[i].strip():
                result.append(('text', parts[i].strip()))
        elif i % 3 == 1:  # Code block or snippets parts
            language = parts[i]
            content = parts[i + 1]
            result.append(('snippet_or_tool', language, content.strip()))

    return result


def parse_tool_json(text):
    try:
        return json5.loads(text)
    except ValueError:
        return None


def print_formatted_content(content):
    content_parts = split_text_and_code(content)

    for part in content_parts:
        if part[0] == 'text':
            print_formatted(content=part[1], color="dark_grey")
        elif part[0] == 'snippet_or_tool':
            language = part[1]
            code_content = part[2]
            if language == 'json5':    # tool call
                json_data = parse_tool_json(code_content)
                if not json_data:
                    print_formatted("Badly parsed tool json:")
                    print_formatted_code(code=code_content, language="json5")
                    return
                tool = json_data.get('tool')
                tool_input = json_data.get('tool_input', {})
                print_tool_message(tool_name=tool, tool_input=tool_input)
            else:       # code snippet
                print_formatted_code(code=code_content, language=language)


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


def print_formatted_code(code, language, start_line=1, title=''):
    console = Console()

    start_line = safe_int(start_line)

    try:
        lexer = get_lexer_by_name(language or 'text')
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

            snippet_title = title or f"{language.capitalize() if isinstance(language, str) else 'Code'} Snippet"

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

            snippet_title = title or f"{language.capitalize() if isinstance(language, str) else 'Code'} Snippet"

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


def print_tool_message(tool_name, tool_input=None):
    if tool_name == 'ask_human':
        pass
    elif tool_name == 'see_file':
        message = "Looking at the file content..."
        print_formatted(content=message, color='blue', bold=True)
        print_formatted(content=tool_input, color='cyan', bold=True)
    elif tool_name == 'list_dir':
        message = "Listing files in a directory..."
        print_formatted(content=message, color='blue', bold=True)
        print_formatted(content=f'{tool_input}/', color='cyan', bold=True)
    elif tool_name == 'create_file_with_code':
        message = "Let's create new file..."
        language = tool_input['filename'].split(".")[-1]
        print_formatted(content=message, color='blue', bold=True)
        print_formatted_code(code=tool_input['code'], language=language, title=tool_input['filename'])
    elif tool_name == 'insert_code':
        message = f"Let's insert code after line {tool_input['start_line']}"
        language = tool_input['filename'].split(".")[-1]
        print_formatted(content=message, color='blue', bold=True)
        print_formatted_code(code=tool_input['code'], language=language, start_line=tool_input['start_line']+1, title=tool_input['filename'])
    elif tool_name == 'replace_code':
        message = f"Let's insert code on the place of lines {tool_input['start_line']} to {tool_input['end_line']}"
        language = tool_input['filename'].split(".")[-1]
        print_formatted(content=message, color='blue', bold=True)
        print_formatted_code(code=tool_input['code'], language=language, start_line=tool_input['start_line'], title=tool_input['filename'])

    elif tool_name == 'add_task':
        message = "Let's add a task..."
        print_formatted(content=message, color='blue', bold=True)
        print_formatted_code(code=tool_input['task_description'], title=tool_input['task_name'], language='text')
    elif tool_name == 'create_epic':
        message = "Let's create an epic..."
        print_formatted(content=message, color='blue', bold=True)
        print_formatted(content=tool_input, color='cyan', bold=True)

    elif tool_name == 'finish':
        message = "Hurray! The work is DONE!"
        print_formatted(content=message, color='cyan', bold=True)
        print_formatted(content=tool_input, color='blue', bold=True)
    elif tool_name == 'final_response_researcher':
        json_string = json.dumps(tool_input, indent=2)
        print_formatted_code(code=json_string, language='json', title='Files:')
    elif tool_name == 'final_response':
        json_string = json.dumps(tool_input, indent=2)
        print_formatted_code(code=json_string, language='json', title='Instruction:')
    else:
        message = f"Calling {tool_name} tool..."
        print_formatted(content=message, color='blue', bold=True)
        print_formatted(content=tool_input, color='blue', bold=True)
