from agents.researcher_agent import Researcher
from agents.planner_agent import planning
from agents.executor_agent import Executor
import os


def run_clean_coder_pipeline(task, work_dir):
    researcher = Researcher(work_dir)
    file_paths, image_paths = researcher.research_task(task)

    plan = planning(task, file_paths, image_paths, work_dir)

    executor = Executor(file_paths, work_dir)
    executor.do_task(task, plan, file_paths)


if __name__ == "__main__":
    task = """Check all system
"""
    work_dir = os.getenv("WORK_DIR")
    run_clean_coder_pipeline(task, work_dir)
