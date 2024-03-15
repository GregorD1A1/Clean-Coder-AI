from langgraph_coder.langgraph_researcher import research_task
from langgraph_coder.langgraph_planner import Planer
from langgraph_coder.langgraph_executor import Executor, check_file_contents


task = ("for post creation step 3 and 4 make same container around like it is in step 1. keep same style.")

files = research_task(task)
file_contents = check_file_contents(files)

planer = Planer(task, file_contents)
plan = planer.plan()

executor = Executor(files)
executor.do_task(task, plan, file_contents)
