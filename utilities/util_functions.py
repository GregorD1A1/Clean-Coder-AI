import textwrap
from tools.tools import see_file
import re
import json
import os
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())
work_dir = os.getenv("WORK_DIR")


def print_wrapped(content, width=160):
    lines = content.split('\n')
    wrapped_lines = [textwrap.fill(line, width=width) for line in lines]
    wrapped_content = '\n'.join(wrapped_lines)
    print(wrapped_content)


def check_file_contents(files):
    file_contents = str()
    for file_name in files:
        file_content = see_file(file_name)
        file_contents += "File: " + file_name + ":\n\n" + file_content + "\n\n###\n\n"

    return file_contents


def find_tool_json(response):
    match = re.search(r'```json(.*?)```', response, re.DOTALL)

    if match:
        json_str = match.group(1).strip()
        print_wrapped(json_str)
        json_obj = json.loads(json_str)
        return json_obj
    else:
        return None


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