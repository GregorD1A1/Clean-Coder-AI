from agents.researcher_agent import research_task
from agents.planner_agent import planning
from agents.executor_agent import Executor


task = ("In src/assets/scss create file profile.scss. I will have common styles for profile page. "
        "create new style for small text here and move data from 'p' style from views/profile/CoverPage here."
        "improve that style to make it gray.")

message_for_planner, files, file_contents = research_task(task)

plan = planning(message_for_planner)

executor = Executor(files)
executor.do_task(task, plan, file_contents)
