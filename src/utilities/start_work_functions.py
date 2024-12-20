"""
Place here functions that should be called when clean coder is started.
"""
import os
import fnmatch


def read_frontend_feedback_story():
    frontend_feedback_story_path = os.path.join(Work.dir(), '.clean_coder', 'frontend_feedback_story.txt')
    with open(frontend_feedback_story_path, 'r') as file:
        return file.read()


def file_folder_ignored(path, ignore_patterns):
    path = path.rstrip('/')  # Remove trailing slash if present

    for pattern in ignore_patterns:
        pattern = pattern.rstrip('/')  # Remove trailing slash from pattern if present

        if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(f"{path}/", f"{pattern}/"):
            return True

    return False


class CoderIgnore:
    forbidden_files_and_folders = None

    @staticmethod
    def read_coderignore():
        coderignore_path = os.path.join(Work.dir(), '.clean_coder', '.coderignore')
        with open(coderignore_path, 'r') as file:
            return [line.strip() for line in file if line.strip() and not line.startswith('#')]

    @staticmethod
    def get_forbidden():
        if CoderIgnore.forbidden_files_and_folders is None:
            CoderIgnore.forbidden_files_and_folders = CoderIgnore.read_coderignore()
        return CoderIgnore.forbidden_files_and_folders


class Work:
    work_dir = None

    @staticmethod
    def read_work_dir():
        try:
            return os.environ["WORK_DIR"]
        except KeyError:
            raise Exception("Please set up your project folder as WORK_DIR parameter in .env")

    @staticmethod
    def dir():
        if Work.work_dir is None:
            Work.work_dir = Work.read_work_dir()
        return Work.work_dir


if __name__ == '__main__':
    read_frontend_feedback_story()