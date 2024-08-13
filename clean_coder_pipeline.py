from agents.researcher_agent import research_task
from agents.planner_agent import planning
from agents.executor_agent import Executor


def run_clean_coder_pipeline(task, self_approve=False):
    files, file_contents, images = research_task(task)

    plan = planning(task, file_contents, images)

    executor = Executor(files)
    executor.do_task(task, plan, file_contents)


if __name__ == "__main__":
    task = """add reorder tool for project manager tools that will reorder tasks. Here is a part of documentation about reorder:
    
The command updates child_order properties of items in bulk.
Command arguments
Argument 	Required 	Description
Array of Objects    Yes     An array of objects to update. Each object contains two attributes: id of the item to update and child_order, the new order.
	
    curl https://api.todoist.com/sync/v8/sync \
    -H "Authorization: Bearer 0123456789abcdef0123456789abcdef01234567" \
    -d commands=[{"type": "item_reorder", "uuid": "bf0855a3-0138-4b76-b895-88cad8db9edc", "args": {"items": [{"id": 33548402, "child_order": 1}, {"id": 33548401, "child_order": 2}]}}]'


###

previous dev badly done that feature, so I have an error:
'AttributeError: 'TodoistAPI' object has no attribute 'sync''
use api call according to docs instead. do not look for class defenition.
"""

    run_clean_coder_pipeline(task)
