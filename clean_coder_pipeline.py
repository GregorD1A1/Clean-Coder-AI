from agents.researcher_agent import research_task
from agents.planner_agent import planning
from agents.executor_agent import Executor


task = """
I changed name of "Post" folder to "MemorialProfileCreationForm". Names of all files started previousely with "Post" now starting from "MemProf".
Also "PostCreationCategories" folder changed to "MemorialProfileCreationCategories". Introduce changes to the files to make app work again.
"""


files, file_contents, images = research_task(task)

plan = planning(task, file_contents, images)

executor = Executor(files)
executor.do_task(task, plan, file_contents)
