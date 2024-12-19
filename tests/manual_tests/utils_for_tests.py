import os
import shutil


def setup_work_dir(project_files_folder):
    if os.path.exists("sandbox_work_dir"):
        cleanup_work_dir()
    os.makedirs("sandbox_work_dir")
    shutil.copytree(f"projects_files/{project_files_folder}", "sandbox_work_dir", dirs_exist_ok=True)


def cleanup_work_dir():
    shutil.rmtree("sandbox_work_dir")


def get_filenames_in_folder(folder):
    folder_path = f"projects_files/{folder}"
    # Initialize an empty set to store filenames
    filenames = set()

    # List all files in the directory
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path):
            # Add the filename to the set
            filenames.add(file)

    return filenames