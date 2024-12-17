import json
import re
import json5
import textwrap
from termcolor import colored
from rich.panel import Panel
from rich.syntax import Syntax
from rich.console import Console
from rich.padding import Padding
from pygments.util import ClassNotFound
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename


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


def print_formatted_content(response):
    if type(response.content) == str:
        print_formatted(content=response.content, color="dark_grey")
        for tool_call in response.tool_calls:
            print_tool_message(tool_name=tool_call["name"], tool_input=tool_call["args"])
    else:
        for response_part in response.content:
            if response_part["type"] == "text":
                print_formatted(content=response_part["text"], color="dark_grey")
            elif response_part["type"] == "tool_use":
                print_tool_message(tool_name=response_part["name"], tool_input=response_part["input"])


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


def get_lexer(extension):
    try:
        lexer = get_lexer_by_name(extension)
    except ClassNotFound:
        if extension in ['tsx', 'svelte']:
            lexer = get_lexer_by_name('jsx')
        else:
            lexer = get_lexer_by_name('text')
    return lexer


def print_code_snippet(code, extension, start_line=1, title=None):
    console = Console()

    lexer = get_lexer(extension)

    syntax = Syntax(
        code,
        lexer,
        line_numbers=True,
        start_line=start_line,
        theme="monokai",
        word_wrap=True,
        padding=(1, 1),
    )

    snippet_title = title or f"{extension.capitalize()} Snippet"
    if len(snippet_title) > 100:
        snippet_title = f"..{snippet_title[-95:]}"

    styled_code = Panel(
        syntax,
        border_style="bold yellow",
        title=snippet_title,
        expand=False
    )
    console.print(Padding(styled_code, 1))


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
        print_formatted(content=tool_input, color='cyan', bold=True)
    elif tool_name == 'create_file_with_code':
        message = "Let's create new file..."
        extension = tool_input['filename'].split(".")[-1]
        print_formatted(content=message, color='blue', bold=True)
        print_code_snippet(code=tool_input['code'], extension=extension, title=tool_input['filename'])
    elif tool_name == 'insert_code':
        message = f"Let's insert code after line {tool_input['start_line']}"
        extension = tool_input['filename'].split(".")[-1]
        print_formatted(content=message, color='blue', bold=True)
        print_code_snippet(code=tool_input['code'], extension=extension, start_line=tool_input['start_line'] + 1, title=tool_input['filename'])
    elif tool_name == 'replace_code':
        message = f"Let's insert code on the place of lines {tool_input['start_line']} to {tool_input['end_line']}"
        extension = tool_input['filename'].split(".")[-1]
        print_formatted(content=message, color='blue', bold=True)
        print_code_snippet(code=tool_input['code'], extension=extension, start_line=tool_input['start_line'], title=tool_input['filename'])

    elif tool_name == 'add_task':
        message = "Let's add a task..."
        print_formatted(content=message, color='blue', bold=True)
        print_code_snippet(code=tool_input['task_description'], title=tool_input['task_name'], extension='text')
    elif tool_name == 'create_epic':
        message = "Let's create an epic..."
        print_formatted(content=message, color='blue', bold=True)
        print_formatted(content=tool_input, color='cyan', bold=True)

    elif tool_name == 'final_response_researcher':
        json_string = json.dumps(tool_input, indent=2)
        print_code_snippet(code=json_string, extension='json', title='Files:')
    elif tool_name == 'final_response_executor':
        message = "Hurray! The work is DONE!"
        print_formatted(content=message, color='cyan', bold=True)
        if isinstance(tool_input, str):
            print_code_snippet(code=tool_input, extension='text', title='Instruction:')
        else:
            print_code_snippet(code=tool_input["test_instruction"], extension='text', title='Instruction:')
    elif tool_name == 'final_response_debugger':
        if isinstance(tool_input, str):
            print_code_snippet(code=tool_input, extension='text', title='Instruction:')
        else:
            print_code_snippet(code=tool_input["test_instruction"], extension='text', title='Instruction:')
        print_formatted("Have any questions about Clean Coder or want to share your experience? Check out our Discord server https://discord.com/invite/8gat7Pv7QJ 😉", color='green')
    else:
        message = f"Calling {tool_name} tool..."
        print_formatted(content=message, color='blue', bold=True)
        print_formatted(content=tool_input, color='blue', bold=True)


if __name__ == '__main__':
   pass