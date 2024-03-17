from langgraph_coder.langgraph_researcher import research_task
from langgraph_coder.langgraph_planner import Planer
from langgraph_coder.langgraph_executor import Executor, check_file_contents


task = ("check if creation step 2 (located in components)is optimal written.")


files = research_task(task)
file_contents = check_file_contents(files)

planer = Planer(task, file_contents)
plan = planer.plan()

#file_contents = "dzikie dinożarły"
#plan = "finish work and go home."
#files = ["src/components/PostCreationStep2.vue"]

executor = Executor(files)
executor.do_task(task, plan, file_contents)
