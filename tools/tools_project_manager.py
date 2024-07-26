from langchain.tools import tool
from todoist_api_python.api import TodoistAPI
import os

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

todoist_api = TodoistAPI(os.getenv('TODOIST_API_KEY'))
PROJECT_ID = os.getenv('TODOIST_PROJECT_ID')


@tool
def get_project_tasks():
    """Get all tasks from project management platform (Todoist).
    tool_input:
    {}
    """
    tasks = todoist_api.get_tasks(project_id=PROJECT_ID)
    return [{'id': task.id, 'name': task.content, 'description': task.description} for task in tasks]


@tool
def add_task(task_name, task_description):
    """Add new task to project management platform (Todoist).
    tool_input:
    :param task_name: name of the task.
    :param task_description: detailed description of what needs to be done in order to implement task.
    """
    task = todoist_api.add_task(project_id=PROJECT_ID, content=task_name, description=task_description)
    return {"status": "Task added successfully", "task_id": task.id}


@tool
def modify_task(task_id, new_task_name=None, new_task_description=None):
    """Modify task in project management platform (Todoist).
    tool_input:
    :param task_id: id of the task.
    :param new_task_name: new name of the task (optional).
    :param new_task_description: new detailed description of what needs to be done in order to implement task (optional).
    """
    update_data = {}
    if new_task_name:
        update_data['content'] = new_task_name
    if new_task_description:
        update_data['description'] = new_task_description
    if update_data:
        todoist_api.update_task(task_id=task_id, **update_data)
    return {"status": "Task modified successfully"}


@tool
def delete_task(task_id):
    """Delete task in project management platform (Todoist).
    tool_input:
    :param task_id: id of the task.
    """
    todoist_api.delete_task(task_id=task_id)
    return {"status": "Task deleted successfully"}


@tool
def mark_task_as_done(task_id):
    """Mark task as done in project management platform (Todoist).
    tool_input:
    :param task_id: id of the task.
    """
    todoist_api.close_task(task_id=task_id)
    return {"status": "Task marked as done successfully"}


@tool
def ask_programmer_to_execute_task(task_id):
    """Ask programmer to implement given task.
    tool_input:
    :param task_id: id of the task.
    """
    raise NotImplementedError


@tool
def ask_tester_to_check_if_change_been_implemented_correctly(query):
    """Ask tester to check if changes have been implemented correctly.
    tool_input:
    :param query: write detailed query to the tester, asking what you want him to test.
    """
    input(query)
    # push to git after check been confirmed
    raise NotImplementedError


if __name__ == "__main__":
    #print(add_task.invoke({"task_name": "dzik.py", "task_description": "pies"}))
    #print(mark_task_as_done({"task_id": 8240143331}))
    print(get_project_tasks({}))

