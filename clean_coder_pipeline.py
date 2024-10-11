if __name__ == "__main__":
    from utilities.graphics import print_ascii_logo
    print_ascii_logo()

from agents.researcher_agent import Researcher
from agents.planner_agent import planning
from agents.executor_agent import Executor
import os
from utilities.user_input import user_input
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


def run_clean_coder_pipeline(task, work_dir):
    researcher = Researcher(work_dir)
    file_paths, image_paths = researcher.research_task(task)

    plan = planning(task, file_paths, image_paths, work_dir)

    executor = Executor(file_paths, work_dir)
    executor.do_task(task, plan, file_paths)


if __name__ == "__main__":
    task = user_input("Provide task to be executed. ")
    work_dir = os.getenv("WORK_DIR")
    run_clean_coder_pipeline(task, work_dir)
