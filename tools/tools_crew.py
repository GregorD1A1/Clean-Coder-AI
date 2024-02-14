from langchain.tools import tool
from pydantic import BaseModel, Field
from typing_extensions import Annotated
import os
import json


default_path = 'takzyli-backend/'


@tool
def list_dir(directory):
    """List files in directory."""
    files = os.listdir(default_path + directory)
    return files


@tool
def see_file(filename):
    """Check contents of file."""
    with open(default_path + filename, 'r') as file:
        lines = file.readlines()
    formatted_lines = [f"{i+1}:{line}" for i, line in enumerate(lines)]
    file_contents = "".join(formatted_lines)

    return file_contents


@tool
def insert_code(payload):
    """Insert new piece of code in provided file. Proper indentation is important.
    :param payload: str, a string representation of json containing the following keys:
        filename: Name and path of file to change.
        line_number: Line number to insert new code after.
        code: Code to insert in the file.
    """
    payload = json.loads(payload)
    filename = payload['filename']
    line_number = int(payload['line_number'])
    code = payload['code']

    with open(default_path + filename, 'r+') as file:
        file_contents = file.readlines()
        file_contents.insert(line_number, code + '\n')
        file.seek(0)
        file.truncate()
        file.write("".join(file_contents))
    return "Code inserted"


@tool
def modify_code(payload):
    """Replace old piece of code with new one. Proper indentation is important.
    :param payload: str, a string representation of json containing the following keys:
        filename: Name and path of file to change.
        start_line: Start line number to replace with new code.
        end_line: End line number to replace with new code.
        new_code: New piece of code to replace old one.
    """
    print(payload)
    payload = json.loads(payload)
    start_line = int(payload['start_line'])
    end_line = int(payload['end_line'])
    with open(default_path + payload['filename'], 'r+') as file:
        file_contents = file.readlines()
        file_contents[start_line - 1:end_line] = [payload['new_code'] + '\n']
        file.seek(0)
        file.truncate()
        file.write("".join(file_contents))
    return "Code modified"


@tool
def check_application_logs(dummy_param):
    """Check out fastapi logs to see if application works correctly."""
    with open(default_path + 'backend.log', 'r') as file:
        logs = file.read()
    return logs
