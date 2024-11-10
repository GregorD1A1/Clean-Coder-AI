import os
import fnmatch
from utilities.user_input import user_input
from utilities.print_formatters import print_formatted
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())
try:
    work_dir = os.environ["WORK_DIR"]
except KeyError:
    raise Exception("Please set up your project folder as WORK_DIR parameter in .env")


def create_coderignore():
    coderignore_path = os.path.join(work_dir, '.clean_coder', '.coderignore')
    default_ignore_content = ".env\n.git/\n.idea/\n.clean_coder/\n.vscode\n.gitignore\nnode_modules/\nvenv/\nenv/\n __pycache__\n*.pyc\n*.log"
    os.makedirs(os.path.dirname(coderignore_path), exist_ok=True)
    if not os.path.exists(coderignore_path):
        with open(coderignore_path, 'w', encoding='utf-8') as file:
            file.write(default_ignore_content)
        print_formatted(".coderignore file created successfully.", color="green")


def read_coderignore():
    coderignore_path = os.path.join(work_dir, '.clean_coder', '.coderignore')
    with open(coderignore_path, 'r') as file:
        return [line.strip() for line in file if line.strip() and not line.startswith('#')]


def read_frontend_feedback_story():
    frontend_feedback_story_path = os.path.join(work_dir, '.clean_coder', 'frontend_feedback_story.txt')
    with open(frontend_feedback_story_path, 'r') as file:
        return file.read()


def file_folder_ignored(path, ignore_patterns):
    path = path.rstrip('/')  # Remove trailing slash if present

    for pattern in ignore_patterns:
        pattern = pattern.rstrip('/')  # Remove trailing slash from pattern if present

        if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(f"{path}/", f"{pattern}/"):
            return True

    return False


def create_project_description_file():
    project_description_path = os.path.normpath(os.path.join(work_dir, '.clean_coder', 'project_description.txt'))
    project_description = user_input("Describe your project in as much detail as possible here.")
    with open(project_description_path, 'w', encoding='utf-8') as file:
        file.write(project_description)
    print_formatted(f"Project description saved. You can edit it in {project_description_path}.", color="green")
    return project_description


def set_up_dot_clean_coder_dir():
    create_coderignore()


# Create .coderignore file with default values if it doesn't exist
set_up_dot_clean_coder_dir()
forbidden_files_and_folders = read_coderignore()
