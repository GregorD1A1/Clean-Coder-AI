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
    task = """Let's add voice support for the 'ask_haman' tool. When tool asks human to write his feedback, add keybord shortcut that will activate microphone listening.
during listening provide buttons to finish recording and to cancel recording. After recording is done, transcribe it with wisper model (use langchain to call it).
Next, paste transcription into input string, allowing human further editing.

Previous programmer done that task badly. now afrer ctrl+S (saving) is clicked (which should end the recording), recording just started. it record for next 5 seconds. this is not expected behaviour, record should stard at ctrl+r and end at ctrl+S. Without predefined length of record
"""
    work_dir = os.getenv("WORK_DIR")
    run_clean_coder_pipeline(task, work_dir)
