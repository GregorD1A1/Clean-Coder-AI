import textwrap
from tools.tools import see_file
import re
import json
import os
from dotenv import load_dotenv, find_dotenv
import xml.etree.ElementTree as ET
from xml.dom.minidom import parse, parseString


load_dotenv(find_dotenv())
work_dir = os.getenv("WORK_DIR")
log_file_path = os.getenv("LOG_FILE")


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
        json_obj = json.loads(json_str)
        return json_obj
    else:
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
            return "ok"
        else:
            return logs
    except Exception as e:
        return f"{type(e).__name__}: {e}"


def read_project_knowledge():
    if os.path.exists(work_dir + ".clean_coder"):
        with open(work_dir + ".clean_coder/researcher_project_knowledge.prompt", "r") as f:
            project_knowledge = f.read()
    else:
        project_knowledge = "None"

    return project_knowledge