import re
import json5
import os
import textwrap
from dotenv import load_dotenv, find_dotenv
import xml.etree.ElementTree as ET
from termcolor import colored
from todoist_api_python.api import TodoistAPI
import base64
import requests



load_dotenv(find_dotenv())
work_dir = os.getenv("WORK_DIR")
log_file_path = os.getenv("LOG_FILE")
todoist_api = TodoistAPI(os.getenv('TODOIST_API_KEY'))
PROJECT_ID = os.getenv('TODOIST_PROJECT_ID')


def print_formatted(content, width=None, color=None, on_color=None, bold=False, end='\n'):
    if width:
        lines = content.split('\n')
        lines = [textwrap.fill(line, width=width) for line in lines]
        content = '\n'.join(lines)
    if bold:
        content = f"\033[1m{content}\033[0m"
    if color:
        content = colored(content, color, on_color=on_color, force_color='True')
    print(content, end=end)


def check_file_contents(files, work_dir):
    file_contents = str()
    for file_name in files:
        file_content = watch_file(file_name, work_dir)
        file_contents += file_content + "\n\n###\n\n"

    return file_contents


def watch_file(filename, work_dir):
    #if file_folder_ignored(filename, forbidden_files_and_folders):
    #    return "You are not allowed to work with this file."
    try:
        with open(join_paths(work_dir, filename), 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        return "File not exists."
    formatted_lines = [f"{i+1}|{line[:-1]}\n" for i, line in enumerate(lines)]
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
