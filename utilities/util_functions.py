import re
import json5
import os
import xml.etree.ElementTree as ET
import base64
import requests
from utilities.start_project_functions import file_folder_ignored, forbidden_files_and_folders

from dotenv import load_dotenv, find_dotenv
from todoist_api_python.api import TodoistAPI

load_dotenv(find_dotenv())
work_dir = os.getenv("WORK_DIR")
log_file_path = os.getenv("LOG_FILE")
todoist_api = TodoistAPI(os.getenv('TODOIST_API_KEY'))
PROJECT_ID = os.getenv('TODOIST_PROJECT_ID')


def check_file_contents(files, work_dir, line_numbers=True):
    file_contents = str()
    for file_name in files:
        file_content = watch_file(file_name, work_dir, line_numbers)
        file_contents += file_content + "\n\n###\n\n"

    return file_contents


def watch_file(filename, work_dir, line_numbers=True):
    if file_folder_ignored(filename, forbidden_files_and_folders):
        return "You are not allowed to work with this file."
    try:
        with open(join_paths(work_dir, filename), 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        return "File not exists."
    if line_numbers:
        formatted_lines = [f"{i + 1}|{line[:-1]}\n" for i, line in enumerate(lines)]
    else:
        formatted_lines = [f"{line[:-1]}\n" for line in lines]
    file_content = "".join(formatted_lines)
    file_content = filename + ":\n\n" + file_content

    return file_content


def find_tools_json(response):
    matches = re.findall(r'```(?:json|json5)\s*\n(.*?)\n\s*```', response, re.DOTALL)

    if not matches:
        return "No json found in response."

    results = []
    for match in matches:
        json_str = match.strip()
        try:
            json5_obj = json5.loads(json_str)
            results.append(json5_obj)
        except:
            results.append("Invalid json.")

    return results


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
        # output = {child.tag: child.text for child in root}
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


def see_image(filename, work_dir):
    try:
        with open(join_paths(work_dir, filename), 'rb') as image_file:
            img_encoded = base64.b64encode(image_file.read()).decode("utf-8")
        return img_encoded
    except Exception as e:
        return f"{type(e).__name__}: {e}"


def convert_images(image_paths):
    images = [
                 {"type": "text", "text": image_path}
                 for image_path in image_paths
             ] + [
                 {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{see_image(image_path, work_dir)}"}}
                 for image_path in image_paths
             ]
    # images for claude
    '''
    images.append(
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": see_image(image_path, work_dir),
            },
        }
    )
    '''
    return images


def join_paths(*args):
    leading_slash = '/' if args[0].startswith('/') else ''
    joined = leading_slash + '/'.join(p.strip('/') for p in args)
    return os.path.normpath(joined)


def get_joke():
    try:
        response = requests.get("https://v2.jokeapi.dev/joke/Programming?type=single")
        # response = requests.get("https://uselessfacts.jsph.pl//api/v2/facts/random")
        joke = response.json()["joke"] + "\n\n"
    except Exception as e:
        joke = f"Failed to receive joke :/"
    return joke


def list_directory_tree(work_dir):
    tree = []
    for root, dirs, files in os.walk(work_dir):
        # Filter out forbidden directories and files
        dirs[:] = [d for d in dirs if not file_folder_ignored(d, forbidden_files_and_folders)]
        files = [f for f in files if not file_folder_ignored(f, forbidden_files_and_folders)]
        rel_path = os.path.relpath(root, work_dir)
        depth = rel_path.count(os.sep)
        indent = "│ " * depth

        # Add current directory to the tree
        tree.append(f"{indent}{'└──' if depth > 0 else ''}📁 {os.path.basename(root)}")

        # Check if the total number of items exceeds the threshold
        total_items = len(dirs) + len(files)
        if total_items > 30:
            file_indent = "│ " * (depth + 1)
            tree.append(f"{file_indent}Too many files/folders to display ({total_items} items)")
            dirs.clear()
            continue

        # Add files to the tree
        file_indent = "│ " * (depth + 1)
        for i, file in enumerate(files):
            connector = "└── " if i == len(files) - 1 else "├── "
            tree.append(f"{file_indent}{connector}{file}")

    return "Content of directory tree:\n" + "\n".join(tree)


def render_tools(tools) -> str:
    from inspect import signature
    descriptions = []
    for tool in tools:
        if hasattr(tool, "func") and tool.func:
            sig = signature(tool.func)
            description = f"tool_name: {tool.name}{sig}\n{tool.description}"
        else:
            description = f"{tool.name} - {tool.description}"

        descriptions.append(description)
    return "\n+++\n".join(descriptions)


def invoke_tool(tool_call, tools):
    tool_name_to_tool = {tool.name: tool for tool in tools}
    name = tool_call["name"]
    requested_tool = tool_name_to_tool[name]

    return requested_tool.invoke(tool_call["arguments"])


if __name__ == "__main__":
    print(list_directory_tree(work_dir))
