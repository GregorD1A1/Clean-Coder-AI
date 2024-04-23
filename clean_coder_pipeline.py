from agents.researcher_agent import research_task
from agents.planner_agent import planning
from agents.executor_agent import Executor


task = ("Create new WorkPage in memorial profiel view. use common styles from assets/scss/MemorialProfile.scss"
        "Use background image from assets/images. "
        "Take a look at EducationPage (mem prof folder) to understand how to style your page.")

files, file_contents, images = research_task(task)

plan = planning(task, file_contents, images)

executor = Executor(files)
executor.do_task(task, plan, file_contents)
