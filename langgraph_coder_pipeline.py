from langgraph_coder.langgraph_researcher import research_task
from langgraph_coder.langgraph_planner import Planer
from langgraph_coder.langgraph_executor import Executor, check_file_contents


task = ("Improve drag and drop component. For now, I see only two fields to manua file select. Add here drag and drop square.")


files = research_task(task)
file_contents = check_file_contents(files)

planer = Planer(task, file_contents)
plan = planer.plan()

executor = Executor(files)
executor.do_task(task, plan, file_contents)
