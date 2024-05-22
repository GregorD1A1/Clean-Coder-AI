from agents.researcher_agent import research_task
from agents.planner_agent import planning
from agents.executor_agent import Executor


task = """
Improve gallery page (memorial profile) to look like in the design. make images bigger, and look like in design, in two lines. improve writing.
"""


files, file_contents, images = research_task(task)

plan = planning(task, file_contents, images)

executor = Executor(files)
executor.do_task(task, plan, file_contents)
