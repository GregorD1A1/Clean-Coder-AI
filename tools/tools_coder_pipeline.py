from langchain.tools import tool
import os
import playwright
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from utilities.syntax_checker_functions import check_syntax
from utilities.start_project_functions import file_folder_ignored, forbidden_files_and_folders
from utilities.util_functions import join_paths
from utilities.user_input import user_input
from rag.retrieval import retrieve


load_dotenv(find_dotenv())
OAIclient = OpenAI()


TOOL_NOT_EXECUTED_WORD = "Tool not been executed. "
#SUCCESSFUL_EXECUTION_WORD = "Tool been executed successfully."

syntax_error_insert_code = """
Changes can cause next error: {error_response}. Probably you:
- Provided a wrong line number to insert code, or
- Forgot to add an indents on beginning of code.
Please analyze which place is correct to introduce the code before calling a tool.
"""
syntax_error_modify_code = """
Changes can cause next error: {error_response}. Probably you:
- Provided a wrong end or beginning line number (end code line happens more often), or
- Forgot to add an indents on beginning of code.
Think step by step which function/code block you want to change before proposing improved change.
"""



def prepare_list_dir_tool(work_dir):
    @tool
    def list_dir(directory):
        """
List files in directory.
tool input:
:param directory: Name of directory to list files in.
"""
        try:
            if file_folder_ignored(directory, forbidden_files_and_folders):
                return f"You are not allowed to work with directory {directory}."
            files = os.listdir(join_paths(work_dir, directory))

            return f"Content of directory {directory}:\n" + "\n".join(files)
        except Exception as e:
            return f"{type(e).__name__}: {e}"

    return list_dir

def prepare_see_file_tool(work_dir):
    @tool
    def see_file(filename):
        """
Check contents of file.
tool input:
:param filename: Name and path of file to check.
"""
        try:
            if file_folder_ignored(filename, forbidden_files_and_folders):
                return f"You are not allowed to work with {filename}."
            with open(join_paths(work_dir, filename), 'r', encoding='utf-8') as file:
                lines = file.readlines()
            formatted_lines = [f"{i+1}|{line[:-1]}\n" for i, line in enumerate(lines)]
            file_content = "".join(formatted_lines)
            file_content = filename + ":\n\n" + file_content

            return file_content
        except Exception as e:
            return f"{type(e).__name__}: {e}"

    return see_file


@tool
def retrieve_files_by_semantic_query(query):
    """
Use that function to find files or folders in the app by text search.
You can search for example for common styles, endpoint with user data, etc.
Useful, when you know what do you look for, but don't know where.

Use that function at least once BEFORE calling final response to ensure you found all appropriate files.

tool input:
:param query: Semantic query describing subject you looking for in one sentence. Ask for a singe thing only.
Explain here thing you look only: good query is "<Thing I'm looking for>", bad query is "Find a files containing <thing I'm looking for>"
"""
    return retrieve(query)


def prepare_insert_code_tool(work_dir):
    @tool
    def insert_code(filename, line_number, code):
        """
Insert new piece of code into provided file. Use when new code need to be added without replacing old one.
Proper indentation is important.
tool input:
:param filename: Name and path of file to change.
:param line_number: Line number to insert new code after.
:param code: Code to insert into the file. Without backticks around. Start it with appropriate indentation if needed.
"""
        try:
            with open(join_paths(work_dir, filename), 'r+', encoding='utf-8') as file:
                file_contents = file.readlines()
                file_contents.insert(line_number, code + '\n')
                file_contents = "".join(file_contents)
                check_syntax_response = check_syntax(file_contents, filename)
                if check_syntax_response != "Valid syntax":
                    print("Wrong syntax provided, asking to correct.")
                    return TOOL_NOT_EXECUTED_WORD + syntax_error_insert_code.format(error_response=check_syntax_response)
                human_message = user_input("Type (o)k if you accept or provide commentary.")
                if human_message not in ['o', 'ok']:
                    return TOOL_NOT_EXECUTED_WORD + f"Action wasn't executed because of human interruption. He said: {human_message}"
                file.seek(0)
                file.truncate()
                file.write(file_contents)
            return "Code inserted."
        except Exception as e:
            return f"{type(e).__name__}: {e}"

    return insert_code


def prepare_replace_code_tool(work_dir):
    @tool
    def replace_code(filename, start_line,  code, end_line):
        """
Replace old piece of code between start_line and end_line with new one. Proper indentation is important.
Avoid changing multiple functions at once.
tool input:
:param filename: Name and path of file to change.
:param start_line: Start line number to replace with new code. Inclusive - means start_line will be first line to change.
:param code: New piece of code to replace old one. Without backticks around. Start it with appropriate indentation if needed.
:param end_line: End line number to replace with new code. Inclusive - means end_line will be last line to change.
"""
        try:
            with open(join_paths(work_dir, filename), 'r+', encoding='utf-8') as file:
                file_contents = file.readlines()
                file_contents[start_line - 1:end_line] = [code + '\n']
                file_contents = "".join(file_contents)
                check_syntax_response = check_syntax(file_contents, filename)
                if check_syntax_response != "Valid syntax":
                    print(check_syntax_response)
                    return TOOL_NOT_EXECUTED_WORD + syntax_error_modify_code.format(error_response=check_syntax_response)
                human_message = user_input("Type (o)k if you accept or provide commentary.")
                if human_message not in ['o', 'ok']:
                    return TOOL_NOT_EXECUTED_WORD + f"Action wasn't executed because of human interruption. He said: {human_message}"
                file.seek(0)
                file.truncate()
                file.write(file_contents)
            return "Code modified."
        except Exception as e:
            return f"{type(e).__name__}: {e}"

    return replace_code


def prepare_create_file_tool(work_dir):
    @tool
    def create_file_with_code(filename, code):
        """
Create new file with provided code. If you need to create directory, all directories in provided path will be
automatically created.

Do not write files longer than 1000 words. If you need to create big files, start small, and next add new functions
with another tools.
tool input:
:param filename: Name and path of file to create.
:param code: Code to write in the file.
"""
        try:
            human_message = user_input("Type (o)k if you accept or provide commentary.")
            if human_message not in ['o', 'ok']:
                return TOOL_NOT_EXECUTED_WORD + f"Action wasn't executed because of human interruption. He said: {human_message}"

            full_path = join_paths(work_dir, filename)
            directory = os.path.dirname(full_path)

            # Create directories if they don't exist
            if not os.path.exists(directory):
                os.makedirs(directory)

            with open(full_path, 'w', encoding='utf-8') as file:
                file.write(code)
            return "File been created successfully."
        except Exception as e:
            return f"{type(e).__name__}: {e}"

    return create_file_with_code


@tool
def ask_human_tool(prompt):
    """
    Ask human to do project setup/debug actions you're not available to do or provide observations of how does program works.
    tool input:
    :param prompt: prompt to human.
    """
    try:
        human_message = user_input(prompt)
        
        return human_message
    except Exception as e:
        return f"{type(e).__name__}: {e}"


# function under development
def make_screenshot(self, endpoint, login_needed, commands):
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

    page.screenshot(path=join_paths(self.work_dir, 'screenshots/screenshot.png'))
    browser.close()


if __name__ == '__main__':
    pass
