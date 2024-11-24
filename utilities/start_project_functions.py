import os
import fnmatch
from utilities.user_input import user_input
from utilities.print_formatters import print_formatted
from dotenv import set_key, load_dotenv, find_dotenv
from os import getenv

try:
    work_dir = os.environ["WORK_DIR"]
except KeyError:
    raise Exception("Please set up your project folder as WORK_DIR parameter in .env")


def dot_env_single_task():
    env_path = find_dotenv()
    if not env_path:
        keys = ["OPENAI_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY", "OLLAMA_MODEL"]
        prompt_for_env_keys(keys)

    load_dotenv(env_path)


def dot_env_manager():
    env_path = find_dotenv()
    if not env_path:
        keys = ["OPENAI_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY", "OLLAMA_MODEL", "TODOIST_API_KEY",
                "TODOIST_PROJECT_ID"]
        prompt_for_env_keys(keys)
    load_dotenv(env_path)


def prompt_for_env_keys(keys):
    env_path = '.env'

    load_dotenv(env_path)

    for key in keys:
        if not getenv(key):
            value = input(f"Provide your {key} (or press enter to skip):")
            if value:
                set_key(env_path, key, value)


def create_coderignore(work_dir):
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


def create_project_description_file():
    project_description_path = os.path.normpath(os.path.join(work_dir, '.clean_coder', 'project_description.txt'))
    project_description = user_input("Describe your project in as much detail as possible here.")
    with open(project_description_path, 'w', encoding='utf-8') as file:
        file.write(project_description)
    print_formatted(f"Project description saved. You can edit it in {project_description_path}.", color="green")
    return project_description


def set_up_dot_clean_coder_dir(work_dir):
    create_coderignore(work_dir)


set_up_dot_clean_coder_dir(work_dir)
forbidden_files_and_folders = read_coderignore()
