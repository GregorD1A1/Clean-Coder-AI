import re
import json
import os
import textwrap
from tools.tools_coder_pipeline import see_file
from dotenv import load_dotenv, find_dotenv
import xml.etree.ElementTree as ET
from termcolor import colored
from todoist_api_python.api import TodoistAPI
from langchain_core.prompts import PromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser


load_dotenv(find_dotenv())
work_dir = os.getenv("WORK_DIR")
log_file_path = os.getenv("LOG_FILE")
todoist_api = TodoistAPI(os.getenv('TODOIST_API_KEY'))
PROJECT_ID = os.getenv('TODOIST_PROJECT_ID')


actualize_description_prompt_template = """After task been executed, actualize description of project progress. 
Write what have been done in the project so far in up to 7 sentences. Never imagine facts. Do not write what need to be 
done in future and do not write project description, if that not needed to describe progress.

Previous progress description, before last task execution:
{progress_description}

Last task been executed:
{task_name_description}

Tester response about task implementation:
{tester_response}

Return new progress description and nothing more.
"""

llm = ChatOpenAI(model="gpt-4o", temperature=0)


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
        print("Multiple jsons found.")
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


def get_project_tasks():
    tasks = todoist_api.get_tasks(project_id=PROJECT_ID)
    tasks_string = "\n".join(
        f"id: {task.id}, \nName: {task.content}, \nDescription: {task.description}, \nOrder: {task.order}\n\n" for task in tasks
    )
    if not tasks:
        tasks_string = "<empty>"
    return "Tasks in Todoist:\n" + tasks_string


def actualize_progress_description_file(task_name_description, tester_response):
    progress_description = read_progress_description()
    actualize_description_prompt = PromptTemplate.from_template(actualize_description_prompt_template)
    chain = actualize_description_prompt | llm | StrOutputParser()
    progress_description = chain.invoke(
        {
            "progress_description": progress_description,
            "task_name_description": task_name_description,
            "tester_response": tester_response
        }
    )
    #print(response.content)
    #response_json = find_tool_json(response.content)
    #progress_description = response_json["tool_input"]["progress_description"]

    with open(os.path.join(work_dir, ".clean_coder", "manager_progress_description.txt"), "w") as f:
        f.write(progress_description)
    print("Writing description of progress done.")


def read_progress_description():
    file_path = os.path.join(work_dir, ".clean_coder", "manager_progress_description.txt")
    if not os.path.exists(file_path):
        open(file_path, 'a').close()  # Creates file if it doesn't exist
        progress_description = "<empty>"
    else:
        with open(file_path, "r") as f:
            progress_description = f.read()
    return progress_description


if __name__ == "__main__":
    print(get_project_tasks())