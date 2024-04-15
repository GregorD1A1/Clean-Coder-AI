from agents.researcher_agent import research_task
from agents.planner_agent import planning
from agents.executor_agent import Executor


task = ("In education page of memorial profile make writings dynamic, as it is in final page")

message_for_planner, files, file_contents = research_task(task)

plan = planning(message_for_planner)

executor = Executor(files)
executor.do_task(task, plan, file_contents)
