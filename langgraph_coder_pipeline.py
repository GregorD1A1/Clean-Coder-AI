from langgraph_coder.langgraph_researcher import research_task
from langgraph_coder.langgraph_planner import Planer
from langgraph_coder.langgraph_executor import Executor, check_file_contents


task = ("In post creation step 2 drag and drop field imported, but I can't see that. Please check out what's wrong with it.")


files = research_task(task)
file_contents = check_file_contents(files)

planer = Planer(task, file_contents)
plan = planer.plan()

executor = Executor(files)
executor.do_task(task, plan, file_contents)
