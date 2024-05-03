from agents.researcher_agent import research_task
from agents.planner_agent import planning
from agents.executor_agent import Executor


task = """
Let's make "edytuj" button in the dashboard to make it edit the profile actually.
"""

files, file_contents, images = research_task(task)

plan = planning(task, file_contents, images)

executor = Executor(files)
executor.do_task(task, plan, file_contents)
