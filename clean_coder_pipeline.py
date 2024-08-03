from agents.researcher_agent import research_task
from agents.planner_agent import planning
from agents.executor_agent import Executor


def run_clean_coder_pipeline(task, self_approve=False):
    files, file_contents, images = research_task(task)

    plan = planning(task, file_contents, images)

    executor = Executor(files)
    executor.do_task(task, plan, file_contents)


if __name__ == "__main__":
    task = """dzik
"""

    run_clean_coder_pipeline(task)
