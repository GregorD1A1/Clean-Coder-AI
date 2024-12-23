import os, sys
from manual_tests.utils_for_tests import setup_work_dir, cleanup_work_dir, get_filenames_in_folder
from src.agents.debugger_agent import Debugger
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


folder_with_project_files = "debugger_scenario_1_files"
setup_work_dir(folder_with_project_files)
files = get_filenames_in_folder(folder_with_project_files)
human_feedback = "Human feedback: Remove some code from the styles. It's too much of code now, let's optimize it."

debugger = Debugger(files, "sandbox_work_dir", human_feedback)

task = "Make form wider, with green background. Improve styling."
plan = """To make the form wider and change its background color to green, we need to modify the CSS file `profileEditStyles.css`. Here are the changes needed:

### profileEditStyles.css

```diff
- max-width: 300px;
+ max-width: 500px;

- background-color: #f9f9f9;
+ background-color: #28a745;
```

### Explanation

1. **Form Width**: 
   - The form's `max-width` is increased from `300px` to `500px` to make it wider.

2. **Background Color**: 
   - The `background-color` is changed from `#f9f9f9` (light grey) to `#28a745` (green) to give the form a green background.

These changes will ensure that the form is wider with a green background, improving its styling as requested. No changes are needed in the `InternProfileEdit.vue` file for this task.
"""  # noqa: E501, W291

debugger.do_task(task, plan)
cleanup_work_dir()
