import os, sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from manual_tests.utils_for_tests import setup_work_dir, cleanup_work_dir, get_filenames_in_folder
from src.agents.planner_agent import planning
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

folder_with_project_files = "planner_scenario_1_files"
setup_work_dir(folder_with_project_files)

task = "Make form wider, with green background. Improve styling."
files = get_filenames_in_folder(folder_with_project_files)

planning(task, files, image_paths={},work_dir="sandbox_work_dir")
cleanup_work_dir()
