from agents.researcher_agent import research_task
from agents.planner_agent import planning
from agents.executor_agent import Executor


task = """
    In SecondPage.vue, replace .location-arrow icon with <v-icon class="icon"> containing mdi-map-marker icon.
"""

files, file_contents, images = research_task(task)

plan = planning(task, file_contents, images)

executor = Executor(files)
executor.do_task(task, plan, file_contents)
