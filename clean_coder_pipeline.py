from agents.researcher_agent import research_task
from agents.planner_agent import planning
from agents.executor_agent import Executor


def run_clean_coder_pipeline(task, self_approve=False):
    files, file_contents, images = research_task(task)
    plan = planning(task, file_contents, images)

    executor = Executor(files)
    executor.do_task(task, plan, file_contents)


if __name__ == "__main__":
    task = """I want manager to write short (up to 6 sentences) information about what been done in the project so far.
Save that information in external txt file (in .clean_coder folder inside of project) and provide it to manager's
context. Every time 'finish_project_planning' tool is executed, information should be actualized on the base of task 
description and tester response. Manager should do that actualization, or at least LLM with manager's context..
"""

    run_clean_coder_pipeline(task)
