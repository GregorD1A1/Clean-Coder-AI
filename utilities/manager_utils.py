from langchain_openai.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from todoist_api_python.api import TodoistAPI
import concurrent.futures
from dotenv import load_dotenv, find_dotenv
import os


load_dotenv(find_dotenv())
work_dir = os.getenv("WORK_DIR")
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


def fetch_epics():
    return todoist_api.get_sections(project_id=PROJECT_ID)


def fetch_tasks():
    return todoist_api.get_tasks(project_id=PROJECT_ID)


def get_project_tasks():
    output_string = ""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_epics = executor.submit(fetch_epics)
        future_tasks = executor.submit(fetch_tasks)

        # Wait for results
        epics = future_epics.result()
        tasks = future_tasks.result()

    for epic in epics:
        output_string += f"## Epic: {epic.name} (id: {epic.id})\n\n"
        tasks_in_epic = [task for task in tasks if task.section_id == epic.id]
        if tasks_in_epic:
            output_string += "\n".join(
                f"Task:\nid: {task.id}, \nName: {task.content}, \nDescription: \n'''{task.description}''', \nOrder: {task.order}\n\n"
                for task in tasks_in_epic
            )
        else:
            output_string += f"No tasks in epic '{epic.name}'\n\n"
    tasks_without_epic = [task for task in tasks if task.section_id is None]
    if tasks_without_epic:
        output_string += "## Tasks without epic:\n\n"
        output_string += "\n".join(
            f"Task:\nid: {task.id}, \nName: {task.content}, \nDescription: \n'''{task.description}''', \nOrder: {task.order}\n"
            for task in tasks_without_epic
        )
    output_string += "\n###\n"
    if not tasks:
        output_string = "<empty>"
    return output_string


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
