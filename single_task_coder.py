if __name__ == "__main__":
    from utilities.graphics import print_ascii_logo
    print_ascii_logo()
from dotenv import find_dotenv
from utilities.set_up_dotenv import set_up_env_coder_pipeline
if not find_dotenv():
    set_up_env_coder_pipeline()

from agents.researcher_agent import Researcher
from agents.planner_agent import planning
from agents.executor_agent import Executor
from agents.debugger_agent import Debugger
from agents.frontend_feedback import write_screenshot_codes, execute_screenshot_codes
import os
from utilities.user_input import user_input
from utilities.print_formatters import print_formatted
from utilities.start_project_functions import set_up_dot_clean_coder_dir
from utilities.util_functions import create_frontend_feedback_story
from concurrent.futures import ThreadPoolExecutor


use_frontend_feedback = bool(os.getenv("FRONTEND_PORT"))


def run_clean_coder_pipeline(task, work_dir):
    researcher = Researcher(work_dir)
    file_paths, image_paths = researcher.research_task(task)

    plan = planning(task, file_paths, image_paths, work_dir)

    executor = Executor(file_paths, work_dir)

    if use_frontend_feedback:
        create_frontend_feedback_story()
        with ThreadPoolExecutor() as executor_thread:
            future = executor_thread.submit(write_screenshot_codes, task, plan, work_dir)
            test_instruction, file_paths = executor.do_task(task, plan)
            playwright_codes, screenshot_descriptions = future.result()
        if playwright_codes:
            print_formatted("Making screenshots, please wait a while...", color="light_blue")
            first_vfeedback_screenshots_msg = execute_screenshot_codes(playwright_codes, screenshot_descriptions)
        else:
            first_vfeedback_screenshots_msg = None
    else:
        test_instruction, file_paths = executor.do_task(task, plan)
        first_vfeedback_screenshots_msg = None

    human_message = user_input("Please test app and provide commentary if debugging/additional refinement is needed.")
    if human_message in ['o', 'ok']:
        return
    debugger = Debugger(file_paths, work_dir, human_message, first_vfeedback_screenshots_msg, playwright_codes, screenshot_descriptions)
    debugger.do_task(task, plan)


if __name__ == "__main__":
    work_dir = os.getenv("WORK_DIR")
    set_up_dot_clean_coder_dir(work_dir)
    task = user_input("Provide task to be executed.")
    run_clean_coder_pipeline(task, work_dir)