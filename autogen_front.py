import autogen
from typing_extensions import Annotated
import os
from flaml.autogen.code_utils import execute_code
from tools.helpers import visual_describe, make_screenshot
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

default_path = '/home/autogen/autogen/takzyli-frontend/'
#default_path = 'E://Autogen_takzyli/takzyli-frontend/'
config_list = [
    #{'base_url': "http://localhost:1234/v1", 'api_key': 'NULL', 'model': 'NULL'}
    {'model': 'gpt-4-1106-preview', 'api_key': os.getenv('OPENAI_API_KEY')},
    ]

gpt4_config = {
    "cache_seed": 40,  # change the cache_seed for different trials
    "temperature": 0,
    "config_list": config_list,
    "timeout": 120,
}

config_list_deepseek = [
    {'base_url': 'http://localhost:8020/', 'api_key': 'NULL'},
]
llm_config_deepseek = {
    'config_list': config_list_deepseek
}

engineer = autogen.AssistantAgent(
    name="Engineer",
    llm_config=gpt4_config,
    system_message='''I'm Engineer.

    I'm working in next pattern:
    Step 1: Research.
    After receiving new task from Admin, I'm checking all the files that I could work on or could be useful.
    Step 2: Planning.
    I'm planning step-by-step how to execute task.My plan includes details about
    what files I'm going to modify and how, including numbers of lines to change. I'm writing all the details which files I'm going to create, which functions
    on which files I'm going to modify. I'm providing concrete names of functions/endpoints etc. 
    After plan is ready, Admin needs to accept it.
    Step 3: If admin accepted plan, I'm choosing one file to create or modify and working with it.
    In case of modification, I'm calling 'modify_code' and 'insert_code' functions for every change. I'm calling first
    bigger line numbers then smaller ones. Also I calling 'check_file' function to control changes.
    Code I'm writing is consistent with code that's already there. I'm strictly forbidden to do anything without a plan.
    If I plan assumes work on more than one file, I'm repeating Step 3 for every of them.
    After job done, confirm that functionality is ready.
    Step 4: Ask tester to check if functionality you introduced works and looks as intended.
    ''',
)
tester = autogen.AssistantAgent(
    name="Tester",
    llm_config=gpt4_config,
    system_message='''I'm Tester. My task is to test frontend features, created by Engineer to provide him feedback.
    
    I'm working in next pattern:
    Step 1: Planning.
    I'm planning step-by-step what features I want to check, where to make screenshots. I'm describing here what
    endpoints I'm going to check and what elements to reference. I'm strictly forbidden imagine new elements or endpoints.
    If I don't know name of endpoint or element, I'm not allowed to proceed in work. I need to write Engineer my
    feedback with questions about lack of provided data and write 'TERMINATE' word to end it.
    If I need to be logged in to check something, go first to /login endpoint and login with: 
    page.fill('#username', 'juraj.kovac@op.pl'), page.fill('#password', 'DnEcZTYB'), 
    page.click('.login-form button[type="submit"]'), next execute rest of the test.
    Step 2: I'm calling function with python playwright code to make screenshot and analyse it with visual AI.
    
    I'm repeating Step 2 for every screenshot, planned in Step 1.
    
    When everything is tested as needed, you writing summarizing note for engineer and ending it with TERMINATE word.
    
    Tested site is running on host.docker.internal:5555
    '''
)

executor = autogen.UserProxyAgent(
    name="Executor",
    human_input_mode="NEVER",
    #max_consecutive_auto_reply=50,
    code_execution_config={"work_dir": "autogen/takzyli-frontend"},
    system_message="Executor. Execute commends and save code created by engineer."
)
user_proxy = autogen.UserProxyAgent(
    name="Admin",
    human_input_mode="ALWAYS",
    system_message="A human admin. Checks Executor after every his move and corrects him.",
    code_execution_config=False,
    is_termination_msg = lambda msg: 'TERMINATE' in msg['content']
)
groupchat = autogen.GroupChat(
    agents=[engineer, user_proxy],
    messages=[],
    max_round=500,
    speaker_selection_method="round_robin",
    enable_clear_history=True,
    )
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=gpt4_config)


# Functions
@user_proxy.register_for_execution()
@engineer.register_for_llm(description="List files in choosen directory.")
def list_dir(directory: Annotated[str, "Directory to check."]):
    files = os.listdir(default_path + directory)
    return 0, files


@user_proxy.register_for_execution()
@engineer.register_for_llm(description="Check the contents of a chosen file.")
def see_file(filename: Annotated[str, "Name and path of file to check."]):
    with open(default_path + filename, 'r') as file:
        lines = file.readlines()
    formatted_lines = [f"{i+1}:{line}" for i, line in enumerate(lines)]
    file_contents = "".join(formatted_lines)

    return 0, file_contents


@user_proxy.register_for_execution()
@engineer.register_for_llm(description="Insert new piece of code in provided file. Proper indentation is important.")
def insert_code(
        filename: Annotated[str, "Name and path of file to change."],
        line_number: Annotated[int, "Line number to insert new code after."],
        code: Annotated[str, "Code to insert in the file. Remember about proper indents."]
):
    with open(default_path + filename, 'r+') as file:
        file_contents = file.readlines()
        file_contents.insert(line_number, code + '\n')
        file.seek(0)
        file.truncate()
        file.write("".join(file_contents))
    return 0, "Code inserted"


def insert_code_old(
        filename: Annotated[str, "Name and path of file to change."],
        position: Annotated[
            str,
            "Existing line or lines of code to insert new code after. Should be unique for all file."
        ],
        code: Annotated[str, "Code to insert in the file."]
):
    with open(default_path + filename, 'r+') as file:
        file_contents = file.readlines()
        new_contents = []
        for line in file_contents:
            if position in line:
                new_contents.append(line + '\n' + code + '\n')
            else:
                new_contents.append(line)
        file.seek(0)
        file.truncate()
        file.write("".join(new_contents))
    return 0, "Code been inserted"


@user_proxy.register_for_execution()
@engineer.register_for_llm(
    description="Replace old piece of code with new one. Proper indentation is important."
)
def modify_code(
        filename: Annotated[str, "Name and path of file to change."],
        start_line: Annotated[int, "Start line number to replace with new code."],
        end_line: Annotated[int, "End line number to replace with new code."],
        new_code: Annotated[str, "New piece of code to replace old_code with. Remember about providing indents."]
):
    with open(default_path + filename, 'r+') as file:
        file_contents = file.readlines()
        file_contents[start_line - 1:end_line] = [new_code + '\n']
        file.seek(0)
        file.truncate()
        file.write("".join(file_contents))
    return 0, "Code modified"


def modify_code_old(
        filename: Annotated[str, "Name and path of file to change."],
        old_code: Annotated[str, "Old piece of code to replace. Should be unique for all file."],
        new_code: Annotated[str, "New piece of code to replace old_code with."]
):
    with open(default_path + filename, 'r+') as file:
        file_contents = file.read()
        modified_contents = file_contents.replace(old_code, new_code)
        file.seek(0)
        file.truncate()  # This is needed to cover all cases where new_code might be shorter than old_code
        file.write(modified_contents)
    return 0, "Code been modified"


@user_proxy.register_for_execution()
@engineer.register_for_llm(description="Create a new file with code.")
def create_file_with_code(
        filename: Annotated[str, "Name and path of file to create."],
        code: Annotated[str, "Code to write in the file."]
):
    with open(default_path + filename, 'w') as file:
        file.write(code)
    return 0, "File created successfully"

@user_proxy.register_for_execution()
@engineer.register_for_llm(description="Ask tester to test functionalities you added.")
def call_tester(
        functionalities: Annotated[str, "Describe here what functionalities tester needs to test"],
        code: Annotated[str, "Provide here code of component to test."],
        endpoint: Annotated[str, "Name of testing endpoint. Never imagine it. Check in router if you don't know."],
        need_to_be_logged: Annotated[bool, "If you need to be logged or not."]
):
    user_proxy.initiate_chat(
        tester,
        message=f"There are functionalities you need to test:\n{functionalities}."
                f"\nEndpoint name: {endpoint}, need to be logged in: {need_to_be_logged}."
                f"Code of the file to test: {code}.",
    )
    final_message = list(tester._oai_messages.values())[0][-1]["content"]
    return 0, final_message



@user_proxy.register_for_execution()
@tester.register_for_llm(
    description="Provide feedback for Engineer by running python playwright code that takes screenshot and "
                "sending screenshot to visual analyser. You are allowed to interact with only elements and endpoints "
                "you seen on the code. If you have no enough info about needed element tags/endpoints, you need to ask"
                "first. Never provide imagined element names or tags or endpoints."
)
def screenshot_visual_analysis(
        endpoint: Annotated[str, "Name of testing endpoint."],
        if_login_needed: Annotated[bool, "If you need to be logged or not."],
        commands: Annotated[str,
        "Commands to execute after goin to endpoint to perform tests. List of dicts with action, selector and optionally"
        " value arguments. action: one of 'fill', 'click', 'hover'. selector: element selector. value: value to fill."
        "Example: [{'action': 'fill', 'selector': '#new-post-title', 'value': 'My New Post'}, "
        "{'action': 'click', 'selector': '#submit-button'}]"],
        prompt_for_visual_analyser: Annotated[str, "Prompt for visual analyser. Provide here exact description what"
                                                   "features do you want to check."]
):
    make_screenshot(endpoint, if_login_needed, commands)
    img_description = visual_describe('/home/autogen/autogen/takzyli-frontend/screenshots/screenshot.png',
                                      prompt_for_visual_analyser)
    return img_description

# End of Functions


user_proxy.initiate_chat(
    manager,
    clear_history=False,
    message="""
You will need to improve app in vue.js. For now, check out all the application files, try to understand it and wait for next instructions.

""",
)
