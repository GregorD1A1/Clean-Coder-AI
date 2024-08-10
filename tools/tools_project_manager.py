from langchain.tools import tool
from todoist_api_python.api import TodoistAPI
import os
from utilities.util_functions import print_wrapped
from dotenv import load_dotenv, find_dotenv
from clean_coder_pipeline import run_clean_coder_pipeline


load_dotenv(find_dotenv())

todoist_api = TodoistAPI(os.getenv('TODOIST_API_KEY'))
PROJECT_ID = os.getenv('TODOIST_PROJECT_ID')



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
Good description include:
- Definition of done (required) - section, describing what need to be done with acceptance criteria.
- Story - user story for a developer explaining why do we want to do this task, why user needs it.
- Resources (optional) - Include here all information that will be helpful for developer to complete task. Example code
you found in internet, files dev need to use, technical details related to existing code dev need to pay attention on.
:param order: order of the task in project.
"""
    task = todoist_api.add_task(project_id=PROJECT_ID, content=task_name, description=task_description, order=order)
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
    """Delete task from project management platform (Todoist) when it's not needed.
tool_input:
:param task_id: id of the task.
"""
    todoist_api.delete_task(task_id=task_id)
    return {"status": "Task deleted successfully"}


@tool
def mark_task_as_done(task_id):
    """Mark task as done in project management platform (Todoist) and save changes to git.
tool_input:
:param task_id: id of the task.
"""
    # TODO: Implement git upload functionality
    # push to git after check has been confirmed
    todoist_api.close_task(task_id=task_id)
    return "Task marked as done successfully"


@tool
def finish_project_planning():
    """Call that tool when all task in Todoist correctly reflect work for nearest time. No extra tasks or tasks with
overlapping scope allowed. Tasks should be in execution order. First task in order will be executed after human acceptance.
tool_input:
{}
"""
    return "Project planning finished"

@tool
def ask_programmer_to_execute_task(task_id):
    """Ask programmer to implement given task.
    tool_input:
    :param task_id: id of the task.
    """
    task = todoist_api.get_task(task_id)
    task_name_description = f"{task.content}\n{task.description}"
    print_wrapped(f"\nAsked programmer to execute task: {task_name_description}\n", color="blue")
    
    # Execute the main pipeline to implement the task
    run_clean_coder_pipeline(task_name_description)
    
    # Ask tester to check if changes have been implemented correctly
    tester_query =  f"""Please check if the task has been implemented correctly.

Task: {task_name_description}
"""
    tester_response = input(tester_query)
    
    return f"Task execution completed. Tester response: {tester_response}"


@tool
def ask_tester_to_check_if_change_been_implemented_correctly(query):
    """Ask tester to check if changes have been implemented correctly.
    tool_input:
    :param query: write detailed query to the tester, asking what you want him to test.
    """
    return input(query)
    # push to git after check been confirmed


@tool
def final_response():
    """Call that tool when task list is complete, ordered, task scopes are not overlapping and first task in order is
precisely described. First task will be executed.
tool input:
{}
"""
    return



if __name__ == "__main__":
    #print(add_task.invoke({"task_name": "dzik.py", "task_description": "pies"}))
    #print(mark_task_as_done({"task_id": 8240143331}))
    print(get_project_tasks({}))

