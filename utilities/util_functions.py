import re
import json
import os
import textwrap
from tools.tools import see_file
from dotenv import load_dotenv, find_dotenv
import xml.etree.ElementTree as ET
from termcolor import colored


load_dotenv(find_dotenv())
work_dir = os.getenv("WORK_DIR")
log_file_path = os.getenv("LOG_FILE")



def print_wrapped(content, width=160, color=None):
    lines = content.split('\n')
    wrapped_lines = [textwrap.fill(line, width=width) for line in lines]
    wrapped_content = '\n'.join(wrapped_lines)
    if color:
        wrapped_content = colored(wrapped_content, color, force_color='True')
    print(wrapped_content)


def check_file_contents(files):
    file_contents = str()
    for file_name in files:
        file_content = see_file(file_name)
        file_contents += file_content + "\n\n###\n\n"

    return file_contents


def find_tool_json(response):
    matches = re.findall(r'```json(.*?)```', response, re.DOTALL)

    if len(matches) == 1:
        json_str = matches[0].strip()
        try:
            json_obj = json.loads(json_str)
            return json_obj
        except json.JSONDecodeError:
            return "Invalid json."
    elif len(matches) > 1:
        return "Multiple jsons found."
    else:
        print("No json found in response.")
        return None


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
        #output = {child.tag: child.text for child in root}
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


def read_project_description():
    file_path = os.path.join(work_dir, ".clean_coder", "project_description.txt")

    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")
        return "None"

    # If the file exists, read the file
    with open(file_path, "r") as f:
        project_knowledge = f.read()

    return project_knowledge
