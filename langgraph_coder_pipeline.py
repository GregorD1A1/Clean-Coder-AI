from langgraph_coder.langgraph_researcher import research_task
from langgraph_coder.langgraph_planner import Planer
from langgraph_coder.langgraph_planner_2 import planning
from langgraph_coder.langgraph_executor import Executor, check_file_contents

"""
task = ("Let's create first page of profile. Use design designed by graphic designer. create new component in src/views named 'CoverPage'. "
        "parameters name, surname, date and place of birth and death should be retreived from backend. Example of backend api call you can see in PostView.vue")
"""
task = "add button 'call the dzik' to the dasboard and next make api request to backend in same format as after post submission"

files = research_task(task)
file_contents = check_file_contents(files)

#planer = Planer(task, file_contents)
#plan = planer.plan()
plan = planning(task, file_contents)

executor = Executor(files)
executor.do_task(task, plan, file_contents)
