from langgraph_coder.langgraph_researcher import research_task
from langgraph_coder.langgraph_planner import Planer


task = "Change database to postgres"
file_contents = research_task(task)
print(file_contents)

planer = Planer(task, file_contents)
plan = planer.plan()
print(plan)

