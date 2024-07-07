from agents.researcher_agent import research_task
from agents.planner_agent import planning
from agents.executor_agent import Executor


task = """
Refractor code. find redundant or ugly-written pieces of code and improve them. Remove unnecesary code.
 find variables, that should be named more clear. Make files and functions shorter and more clear.
"""


files, file_contents, images = research_task(task)

plan = planning(task, file_contents, images)

executor = Executor(files)
executor.do_task(task, plan, file_contents)
