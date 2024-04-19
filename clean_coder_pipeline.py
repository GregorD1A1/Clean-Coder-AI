from agents.researcher_agent import research_task
from agents.planner_agent import planning
from agents.executor_agent import Executor


task = ("when request on answer endpoint arrived, save request parameters and answer in MySQL database. Also, measure "
        "time of response generation and also save it. Database login data:"
        "Server: mysql.mikr.us; login: r217; Haslo: FC6E_d36c57; Baza: db_r217")

message_for_planner, files, file_contents = research_task(task)

plan = planning(message_for_planner)

executor = Executor(files)
executor.do_task(task, plan, file_contents)
