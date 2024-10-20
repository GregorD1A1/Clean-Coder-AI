import os
import fnmatch
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())
work_dir = os.getenv("WORK_DIR")


def create_coderignore():
    coderignore_path = os.path.join(work_dir, '.clean_coder', '.coderignore')
    default_ignore_content = ".env\n.clean_coder/\n.git/\nnode_modules/\n*.pyc\n.vscode/\n.idea/\n.github/\n*.log\nvenv/\n"
    os.makedirs(os.path.dirname(coderignore_path), exist_ok=True)
    if not os.path.exists(coderignore_path):
        with open(coderignore_path, 'w', encoding='utf-8') as file:
            file.write(default_ignore_content)
        print(".coderignore file created successfully.")


def read_coderignore():
    coderignore_path = os.path.join(work_dir, '.clean_coder', '.coderignore')
    with open(coderignore_path, 'r') as file:
        return [line.strip() for line in file if line.strip() and not line.startswith('#')]


def file_folder_ignored(path, ignore_patterns):
    path = path.rstrip('/')  # Remove trailing slash if present

    for pattern in ignore_patterns:
        pattern = pattern.rstrip('/')  # Remove trailing slash from pattern if present

        if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(f"{path}/", f"{pattern}/"):
            return True

    return False

def create_project_discription_file():
    # Create project_description.txt file if it doesn't exist inside of .clean_coder folder
    project_description_path = os.path.join(work_dir, '.clean_coder', 'project_description.txt')
    if not os.path.exists(project_description_path):
        with open(project_description_path, 'w', encoding='utf-8') as file:
            file.write("# Describe your project detailly here: ")


# Create .coderignore file with default values if it doesn't exist
create_coderignore()
forbidden_files_and_folders = read_coderignore()
create_project_discription_file()
