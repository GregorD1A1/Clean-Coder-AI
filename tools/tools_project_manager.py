from langchain.tools import tool
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


# py-trello
@tool
def get_project_tasks():
    """Get all tasks from project management platform (Trello)."""
    raise NotImplementedError


@tool
def add_task(task_name, task_description):
    """Add new task to project management platform (Trello).
    tool_input:
    :param task_name: name of the task.
    :param task_description: detailed description of what needs to be done in order to implement task.
    """
    raise NotImplementedError


@tool
def modify_task(task_id, new_task_name, new_task_description):
    """Modify task in project management platform (Trello).
    tool_input:
    :param task_id: id of the task.
    :param new_task_name: new name of the task.
    :param new_task_description: new detailed description of what needs to be done in order to implement task.
    """
    raise NotImplementedError


@tool
def delete_task(task_id):
    """Delete task in project management platform (Trello).
    tool_input:
    :param task_id: id of the task.
    """
    raise NotImplementedError


def mark_task_as_done(task_id):
    """Mark task as done in project management platform (Trello).
    tool_input:
    :param task_id: id of the task.
    """
    raise NotImplementedError


def ask_programmer_to_execute_task(task_id):
    """Ask programmer to implement given task.
    tool_input:
    :param task_id: id of the task.
    """
    raise NotImplementedError


def ask_tester_to_check_if_change_been_implemented_correctly(query):
    """Ask tester to check if changes have been implemented correctly.
    tool_input:
    :param query: write detailed query to the tester, asking what you want him to test.
    """
    input(query)
    # push to git after check been confirmed
    raise NotImplementedError