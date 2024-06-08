from agents.researcher_agent import research_task
from agents.planner_agent import planning
from agents.executor_agent import Executor


task = """
In dashboard, there is a button "kup profil" make it unclickable. add dymek with "Lista dostępnych domów pogrzebowach będzie dostępna już wkrótce" text when hover over it.
"""


files, file_contents, images = research_task(task)

plan = planning(task, file_contents, images)

executor = Executor(files)
executor.do_task(task, plan, file_contents)
