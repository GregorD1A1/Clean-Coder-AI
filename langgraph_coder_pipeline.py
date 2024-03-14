from langgraph_coder.langgraph_researcher import research_task
from langgraph_coder.langgraph_planner import Planer
from langgraph_coder.langgraph_executor import Executor, check_file_contents


task = ("DCenter content of post creation step 1, maybe add some distance from sides. "
        "Make it same as it done in post creation step 2")

files = research_task(task)
file_contents = check_file_contents(files)

planer = Planer(task, file_contents)
plan = planer.plan()

executor = Executor(files)
executor.do_task(task, plan, file_contents)
