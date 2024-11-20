if __name__ == "__main__":
    from utilities.graphics import print_ascii_logo
    print_ascii_logo()

from utilities.user_input import user_input
from agents.researcher_agent import Researcher
from agents.planner_agent import planning
from agents.executor_agent import Executor
from agents.debugger_agent import Debugger
from utilities.print_formatters import print_formatted


def harvest_website(file_path: str) -> None:
    """Harvest website using scraper code."""
    pass


def pull_documentation_from_internet(work_dir: str, url: str) -> str:
    """Pull documentation from the internet. Includes links of the url page."""
    # TODO: implement.
    documentation = ""
    # file_path = single_clean_coder_pipeline(task, work_dir, url="https://www.selenium.dev/selenium/docs/api/py/api.html",context=None)
    # harvest_website(file_path)
    return documentation


def debug_clean_coder_output(human_message: str,
                 file_paths: set[str],
                 work_dir: str,
                 task,
                 plan) -> str:
    """Debug the executed project change."""
    if human_message in ['o', 'ok']:
        return list(file_paths)[0]
    else:
        while human_message not in ['o', 'ok']:
            debugger = Debugger(file_paths, work_dir, human_message)
            debugger.do_task(task, plan, file_paths)
            human_message = user_input("Please test app and provide commentary if debugging/additional refinement is needed.")
    return list(file_paths)[0]


def single_clean_coder_pipeline(task: str, work_dir: str, url: str, context: str | None) -> str:
    """Prepare web harvest code to collect whole URL (a while loop until successful)."""
    # TODO: enable adding context (newest documentation information)
    # TODO: Single file output is optional.
    researcher = Researcher(work_dir)
    file_paths, image_paths = researcher.research_task(task)
    assert len(file_paths) == 1
    plan = planning(task, file_paths, image_paths, work_dir)

    executor = Executor(file_paths, work_dir)
    test_instruction, file_paths = executor.do_task(task, plan)
    # print_formatted(test_instruction, color="blue")

    human_message = user_input("Please test app and provide commentary if debugging/additional refinement is needed.")
    return debug_clean_coder_output(
        human_message=human_message,
        file_paths=file_paths,
        work_dir=work_dir,
        task=task,
        plan=plan)

