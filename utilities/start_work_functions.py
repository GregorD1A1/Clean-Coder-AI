"""
Place here functions that should be called when clean coder is started.
"""
import os
import fnmatch


try:
    work_dir = os.environ["WORK_DIR"]
except KeyError:
    raise Exception("Please set up your project folder as WORK_DIR parameter in .env")


def read_coderignore():
    coderignore_path = os.path.join(work_dir, '.clean_coder', '.coderignore')
    with open(coderignore_path, 'r') as file:
        return [line.strip() for line in file if line.strip() and not line.startswith('#')]


def read_frontend_feedback_story():
    frontend_feedback_story_path = os.path.join(work_dir, '.clean_coder', 'frontend_feedback_story.txt')
    if os.path.exists(frontend_feedback_story_path):
        with open(frontend_feedback_story_path, 'r') as file:
            return file.read()
    else:
        # handle creation of story file logic
        return "<Story file does not exist."


def file_folder_ignored(path, ignore_patterns):
    path = path.rstrip('/')  # Remove trailing slash if present

    for pattern in ignore_patterns:
        pattern = pattern.rstrip('/')  # Remove trailing slash from pattern if present

        if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(f"{path}/", f"{pattern}/"):
            return True

    return False


forbidden_files_and_folders = read_coderignore()