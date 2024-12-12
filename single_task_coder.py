"""Single coder pipeline."""
if __name__ == "__main__":
    from utilities.graphics import print_ascii_logo

    print_ascii_logo()

import os
import warnings
from venv import logger

from agents.debugger_agent import Debugger
from agents.executor_agent import Executor
from agents.planner_agent import planning
from agents.researcher_agent import Researcher
from utilities.print_formatters import print_formatted
from utilities.user_input import user_input

warnings.filterwarnings("ignore", category=DeprecationWarning)


def run_clean_coder_pipeline(task: str, work_dir: str, extra_logs: int = 0) -> None:
    """Single clean coder pipeline function."""
    researcher = Researcher(work_dir)
    file_paths, image_paths = researcher.research_task(task)

    plan = planning(task, file_paths, image_paths, work_dir)

    executor = Executor(file_paths, work_dir)
    test_instruction, file_paths = executor.do_task(task, plan)
    if extra_logs > 0:
        print_formatted(test_instruction, color="blue")

    human_message = user_input(
        "Please test app and provide commentary if debugging/additional refinement is needed.",
    )
    if human_message in ["o", "ok"]:
        return
    debugger = Debugger(file_paths, work_dir, human_message)
    debugger.do_task(task, plan, file_paths)


if __name__ == "__main__":
    task = user_input("Provide task to be executed.")

    work_dir = os.getenv("WORK_DIR")
    if isinstance(work_dir, str):
        run_clean_coder_pipeline(task, work_dir)
    else:
        logger.info("WORK_DIR environment variable is not set.")
