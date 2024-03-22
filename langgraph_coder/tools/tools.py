from langchain.tools import tool
import os
import json
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())
work_dir = os.getenv("WORK_DIR")


@tool
def list_dir(directory):
    """List files in directory.
    :param directory: Directory to check.
    """
    try:
        files = os.listdir(work_dir + directory)
        return files
    except Exception as e:
        return f"{type(e).__name__}: {e}"

@tool
def see_file(filename):
    """Check contents of file."""
    try:
        with open(work_dir + filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        formatted_lines = [f"{i+1}:{line}" for i, line in enumerate(lines)]
        file_contents = "".join(formatted_lines)

        return file_contents
    except Exception as e:
        return f"{type(e).__name__}: {e}"


@tool
def insert_code(filename, line_number, code):
    """Insert new piece of code into provided file. Proper indentation is important.
    :param filename: Name and path of file to change.
    :param line_number: Line number to insert new code after.
    :param code: Code to insert in the file.
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
def modify_code(filename, start_line, end_line, new_code):
    """Replace old piece of code between start_line and end_line with new one. Proper indentation is important.
    :param filename: Name and path of file to change.
    :param start_line: Start line number to replace with new code. Inclusive.
    :param end_line: End line number to replace with new code. Inclusive.
    :param new_code: New piece of code to replace old one.
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
        return "File was created successfully"
    except Exception as e:
        return f"{type(e).__name__}: {e}"


def check_application_logs():
    """Check out logs to see if application works correctly."""
    try:
        with open(work_dir + 'frontend-build-errors.txt', 'r') as file:
            logs = file.read()
        if logs.strip().endswith("No errors found"):
            print("Logs are correct")
            return "ok"
        else:
            return logs
    except Exception as e:
        return f"{type(e).__name__}: {e}"

if __name__ == "__main__":
    modify_code('test.txt', 1, 3, 'OsiÄ…gniÄ™cia dziki ')