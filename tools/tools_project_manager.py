from langchain.tools import tool
from todoist_api_python.api import TodoistAPI
import os
from utilities.util_functions import print_wrapped, actualize_progress_description_file
from dotenv import load_dotenv, find_dotenv
from clean_coder_pipeline import run_clean_coder_pipeline
import uuid
import requests
import json


load_dotenv(find_dotenv())

todoist_api_key = os.getenv('TODOIST_API_KEY')
todoist_api = TodoistAPI(todoist_api_key)
base_work_dir = os.getenv('WORK_DIR')
PROJECT_ID = os.getenv('TODOIST_PROJECT_ID')
TOOL_NOT_EXECUTED_WORD = "Tool not been executed. "


@tool
def add_task(task_name, task_description, order):
    """Add new task to project management platform (Todoist).
Think very carefully before adding a new task to know what do you want exactly. Explain in detail what needs to be
done in order to execute task.
Avoid creating new tasks that have overlapping scope with old ones - modify or delete old tasks first.
tool_input:
:param task_name: name of the task. Good name is descriptive, starts with a verb and usually could be fitted in formula
'To complete this task, I need to $TASK_NAME'.
:param task_description: detailed description of what needs to be done in order to implement task.
Good description includes:
- Definition of done (required) - section, describing what need to be done with acceptance criteria.
- Resources (optional) - Include here all information that will be helpful for developer to complete task. Example code
you found in internet, files dev need to use, technical details related to existing code programmer need to pay
attention on.
:param order: order of the task in project.
"""
    human_message = input("Write 'ok' if you agree with agent or provide commentary: ")
    if human_message != 'ok':
        return TOOL_NOT_EXECUTED_WORD + f"Action wasn't executed because of human interruption. He said: {human_message}"

    todoist_api.add_task(project_id=PROJECT_ID, content=task_name, description=task_description, order=order)
    return "Task added successfully"


@tool
def modify_task(task_id, new_task_name=None, new_task_description=None):
    """Modify task in project management platform (Todoist).
tool_input:
:param task_id: id of the task.
:param new_task_name: new name of the task (optional).
:param new_task_description: new detailed description of what needs to be done in order to implement task (optional).
"""
    task_name = todoist_api.get_task(task_id).content
    human_message = input(f"I want to modify task '{task_name}'. Write 'ok' if you agree or provide commentary: ")
    if human_message != 'ok':
        return TOOL_NOT_EXECUTED_WORD + f"Action wasn't executed because of human interruption. He said: {human_message}"

    update_data = {}
    if new_task_name:
        update_data['content'] = new_task_name
    if new_task_description:
        update_data['description'] = new_task_description

    todoist_api.update_task(task_id=task_id, **update_data)

    return "Task modified successfully"


@tool
def reorder_tasks(task_items):
    """Reorder tasks in project management platform (Todoist).
    tool_input:
    :param task_items: list of dictionaries with 'id' (str) and 'child_order' (int) keys.
    Example:
    {
    "tool": "reorder_tasks",
    "tool_input": {
        task_items: [
        {"id": "123", "child_order": 0},
        {"id": "456", "child_order": 1},
    ]

}
    """
    command = {
        "type": "item_reorder",
        "uuid": str(uuid.uuid4()),
        "args": {
            "items": task_items
        }
    }
    commands_json = json.dumps([command])
    response = requests.post(
        "https://api.todoist.com/sync/v9/sync",
        headers={"Authorization": f"Bearer {todoist_api_key}"},
        data={"commands": commands_json}
    )
    return "Tasks reordered successfully"


@tool
def delete_task(task_id):
    """Delete task from project management platform (Todoist) when it's not needed.
tool_input:
:param task_id: id of the task.
"""
    task_name = todoist_api.get_task(task_id).content
    human_message = input(f"I want to delete task '{task_name}'. Write 'ok' if you agree or provide commentary: ")
    if human_message != 'ok':
        return TOOL_NOT_EXECUTED_WORD + f"Action wasn't executed because of human interruption. He said: {human_message}"

    todoist_api.delete_task(task_id=task_id)
    return "Task deleted successfully"


@tool
def finish_project_planning():
    """Call that tool when all task in Todoist correctly reflect work for nearest time. No extra tasks or tasks with
overlapping scope allowed. Tasks should be in execution order. First task in order will be executed after human acceptance.
tool_input:
{}
"""
    human_comment = input(
        "Project planning finished. Provide your proposition of changes in the project tasks or write 'ok' to continue...\n"
    )
    if human_comment != "ok":
        return human_comment

    # Get first task and it's name and description
    task = todoist_api.get_tasks(project_id=PROJECT_ID)[0]
    task_name_description = f"{task.content}\n{task.description}"

    # Execute the main pipeline to implement the task
    print_wrapped(f"\nAsked programmer to execute task: {task_name_description}\n", color="blue")
    run_clean_coder_pipeline(task_name_description, base_work_dir)

    # Mark task as done
    todoist_api.close_task(task_id=task.id)

    # ToDo: git upload

    # Ask tester to check if changes have been implemented correctly
    tester_query = f"""Please check if the task has been implemented correctly.

    Task: {task_name_description}
    """
    tester_response = input(tester_query)

    actualize_progress_description_file(task_name_description, tester_response)

    return f"Task execution completed. Tester response: {tester_response}"


if __name__ == "__main__":
    #print(add_task.invoke({"task_name": "dzik.py", "task_description": "pies", "order": 7}))
    """reorder_tasks.invoke([
            {"id": "8285014506", "child_order": 0},
            {"id": "8277686998", "child_order": 1},
            {"id": "8284954420", "child_order": 2},
            {"id": "8277603650", "child_order": 3},
            {"id": "8277604071", "child_order": 4}
        ]
    )"""
    from utilities.util_functions import get_project_tasks
    print(get_project_tasks())
    finish_project_planning.invoke({})
