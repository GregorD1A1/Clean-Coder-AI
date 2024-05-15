import re
import json
import os
import textwrap
from tools.tools import see_file
from dotenv import load_dotenv, find_dotenv
import xml.etree.ElementTree as ET
from termcolor import colored
<<<<<<< HEAD
import ast
=======
from bs4 import BeautifulSoup
import esprima
>>>>>>> 307f1759f7ccea6247b5cb78b8b86329beb4f9ca


load_dotenv(find_dotenv())
work_dir = os.getenv("WORK_DIR")
log_file_path = os.getenv("LOG_FILE")


def print_wrapped(content, width=160, color="black"):
    lines = content.split('\n')
    wrapped_lines = [textwrap.fill(line, width=width) for line in lines]
    wrapped_content = '\n'.join(wrapped_lines)
    print(colored(wrapped_content, color))


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


def read_project_knowledge():
    if os.path.exists(work_dir + ".clean_coder"):
        with open(work_dir + ".clean_coder/researcher_project_knowledge.prompt", "r") as f:
            project_knowledge = f.read()
    else:
        project_knowledge = "None"

    return project_knowledge


def check_syntax(file_content, filename):
    parts = filename.split(".")
    extension = parts[-1] if len(parts) > 1 else ''
    if extension == "py":
        return check_syntax_python(file_content)
    else:
        return "Valid syntax"


def check_syntax_python(code):
    try:
        ast.parse(code)
        return "Valid syntax"
    except SyntaxError as e:
        return f"Syntax Error: {e.msg} (line {e.lineno - 1})"
    except Exception as e:
        return f"Error: {e}"


def parse_html(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        str(soup)  # This forces BS4 to parse and check for errors
        print("HTML syntax appears to be valid.")
    except Exception as e:
        print(f"HTML syntax error: {e}")


def parse_javascript(js_content):
    try:
        esprima.parseScript(js_content)
        print("JavaScript syntax appears to be valid.")
    except esprima.Error as e:
        print(f"JavaScript syntax error: {e}")


def check_vue_file(content):
    # Assuming standard .vue structure
    soup = BeautifulSoup(content, 'html.parser')

    # Extract and check HTML template
    template = soup.find('template')
    if template:
        parse_html(str(template))

    # Extract and check JavaScript
    script = soup.find('script')

    if script:
        parse_javascript(script.text)
