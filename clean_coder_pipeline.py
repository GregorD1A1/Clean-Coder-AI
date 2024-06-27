from agents.researcher_agent import research_task
from agents.planner_agent import planning
from agents.executor_agent import Executor


task = """
Currently page with terms and conditions acceptance shows to the user after login, if he has not done it yet (according to backend flag).
Make it show during login; do not login user until he accepts the terms and conditions.
"""


files, file_contents, images = research_task(task)

plan = planning(task, file_contents, images)

executor = Executor(files)
executor.do_task(task, plan, file_contents)
