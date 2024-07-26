from agents.researcher_agent import research_task
from agents.planner_agent import planning
from agents.executor_agent import Executor


def run_clean_coder_pipeline(task, self_approve=False):
    files, file_contents, images = research_task(task)

    plan = planning(task, file_contents, images)

    executor = Executor(files)
    executor.do_task(task, plan, file_contents)


if __name__ == "__main__":
    task = """
    On the main page there is a search window for a memorial profile. Now it automatically enters myślnik "-" when second and fourth 
    number is entered. It's bad approach; better make myślnik to be entered when third and fifth number is placed, just before the number.
    Ask if you have an additional questions.
    """

    run_clean_coder_pipeline(task)
