if __name__ == "__main__":
    from utilities.graphics import print_ascii_logo
    print_ascii_logo()

from agents.researcher_agent import Researcher
from agents.planner_agent import planning
from agents.executor_agent import Executor
from agents.debugger_agent import Debugger
from agents.frontend_feedback import make_feedback_screenshots
import os
from utilities.user_input import user_input
from utilities.print_formatters import print_formatted
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


def run_clean_coder_pipeline(task, work_dir):
    researcher = Researcher(work_dir)
    file_paths, image_paths = researcher.research_task(task)

    plan = planning(task, file_paths, image_paths, work_dir)

    executor = Executor(file_paths, work_dir)

    if os.environ["FRONTEND_PORT"]:
        with ThreadPoolExecutor() as executor_thread:
            future = executor_thread.submit(make_feedback_screenshots, task, plan, work_dir)
            test_instruction, file_paths = executor.do_task(task, plan)
            vfeedback_screenshots_msg = future.result()
    else:
        test_instruction, file_paths = executor.do_task(task, plan)
        vfeedback_screenshots_msg = None
        #vfeedback_screenshots_msg = make_feedback_screenshots(task, plan, work_dir)

    human_message = user_input("Please test app and provide commentary if debugging/additional refinement is needed.")
    if human_message in ['o', 'ok']:
        return
    debugger = Debugger(file_paths, work_dir, human_message, vfeedback_screenshots_msg)
    debugger.do_task(task, plan, file_paths)


if __name__ == "__main__":
    task = user_input("Provide task to be executed.")
    work_dir = os.getenv("WORK_DIR")
    run_clean_coder_pipeline(task, work_dir)
