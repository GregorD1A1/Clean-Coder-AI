if __name__ == "__main__":
    from src.utilities.graphics import print_ascii_logo
    print_ascii_logo()

from dotenv import find_dotenv, load_dotenv
from src.utilities.set_up_dotenv import set_up_env_manager, add_todoist_envs
import os
if not find_dotenv():
    set_up_env_manager()
elif load_dotenv(find_dotenv()) and not os.getenv("TODOIST_API_KEY"):
    add_todoist_envs()

from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.load import dumps, loads
from langgraph.graph import StateGraph
from dotenv import load_dotenv, find_dotenv
from src.tools.tools_project_manager import add_task, modify_task, create_epic, modify_epic, finish_project_planning, reorder_tasks
from src.tools.tools_coder_pipeline import prepare_list_dir_tool, prepare_see_file_tool, ask_human_tool
from src.utilities.manager_utils import read_project_description, read_progress_description, get_project_tasks
from src.utilities.langgraph_common_functions import call_model, call_tool, multiple_tools_msg, no_tools_msg
from src.utilities.start_project_functions import create_project_description_file, set_up_dot_clean_coder_dir
from src.utilities.util_functions import join_paths
from src.utilities.llms import init_llms
from src.utilities.print_formatters import print_formatted
import json
import os


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]


class Manager:
    def __init__(self):
        load_dotenv(find_dotenv())
        self.work_dir = os.getenv("WORK_DIR")
        set_up_dot_clean_coder_dir(self.work_dir)
        self.tools = self.prepare_tools()
        self.llms = init_llms(self.tools, "Manager")
        self.system_message = self.load_system_message()
        self.manager = self.setup_workflow()
        self.saved_messages_path = join_paths(self.work_dir, ".clean_coder/manager_messages.json")
        self.tasks_progress_template = """Actual list of tasks you planned in Todoist:

{tasks}

###

What have been done so far:
{progress_description}"""
# node functions
    def call_model_manager(self, state):
        self.save_messages_to_disk(state)
        state = call_model(state, self.llms)
        state = self.cut_off_context(state)
        return state

    def call_tool_manager(self, state):
        state = call_tool(state, self.tools)
        state = self.actualize_tasks_list_and_progress_description(state)
        return state

# Logic for conditional edges
    def after_agent_condition(self, state):
        last_message = state["messages"][-1]

        if last_message.content in (multiple_tools_msg, no_tools_msg):
            return "agent"
        else:
            return "tool"

# just functions
    def actualize_tasks_list_and_progress_description(self, state):
        # Remove old tasks message
        state["messages"] = [msg for msg in state["messages"] if not hasattr(msg, "tasks_and_progress_message")]
        # Add new message
        project_tasks = get_project_tasks()
        progress_description = read_progress_description()
        tasks_and_progress_msg = HumanMessage(
            content=self.tasks_progress_template.format(tasks=project_tasks, progress_description=progress_description),
            tasks_and_progress_message=True
        )
        state["messages"].insert(-2, tasks_and_progress_msg)
        return state

    def cut_off_context(self, state):
        approx_nr_msgs_to_save = 30
        if len(state["messages"]) > approx_nr_msgs_to_save:
            last_messages = state["messages"][-approx_nr_msgs_to_save:]

            # Find the index of the first 'ai' message from the end in the last 30 messages
            ai_message_index_in_last_msgs = next((i for i, message in enumerate(last_messages) if message.type == "ai"), None)
            # Calculate the actual index of the 'ai' message in the original list
            ai_message_index = len(state["messages"]) - approx_nr_msgs_to_save + ai_message_index_in_last_msgs
            # Collect all messages starting from the 'ai' message
            last_messages_excluding_system = [msg for msg in state["messages"][ai_message_index:] if msg.type != "system"]

            system_message = state["messages"][0]
            state["messages"] = [system_message] + last_messages_excluding_system

        return state


    def save_messages_to_disk(self, state):
        # remove system message
        messages = state["messages"][1:]
        messages_string = dumps(messages)
        with open(self.saved_messages_path, "w") as f:
            json.dump(messages_string, f)

    def prepare_tools(self):
        list_dir = prepare_list_dir_tool(self.work_dir)
        see_file = prepare_see_file_tool(self.work_dir)
        tools = [
            add_task,
            modify_task,
            reorder_tasks,
            create_epic,
            modify_epic,
            list_dir,
            see_file,
            ask_human_tool,
            finish_project_planning,
        ]
        return tools

    def load_system_message(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(f"{current_dir}/src/prompts/manager_system.prompt", "r") as f:
            system_prompt_template = f.read()

        if os.path.exists(os.path.join(self.work_dir, '.clean_coder/project_description.txt')):
            project_description = read_project_description()
        else:
            project_description = create_project_description_file(self.work_dir)

        return SystemMessage(
            content=system_prompt_template.format(project_description=project_description)
        )

    # workflow definition
    def setup_workflow(self):
        manager_workflow = StateGraph(AgentState)
        manager_workflow.add_node("agent", self.call_model_manager)
        manager_workflow.add_node("tool", self.call_tool_manager)
        manager_workflow.set_entry_point("agent")
        manager_workflow.add_conditional_edges("agent", self.after_agent_condition)
        manager_workflow.add_edge("tool", "agent")
        return manager_workflow.compile()


    def run(self):
        print_formatted("😀 Hello! I'm Manager agent. Let's plan your project together!", color="green")
        if not os.path.exists(self.saved_messages_path):
            # new start
            project_tasks = get_project_tasks()
            progress_description = read_progress_description()
            tasks_and_progress_msg = HumanMessage(
                content=self.tasks_progress_template.format(tasks=project_tasks, progress_description=progress_description),
                tasks_and_progress_message=True
            )
            start_human_message = HumanMessage(content="Go")    # Claude needs to have human message always as first
            messages = [self.system_message, tasks_and_progress_msg, start_human_message]
        else:
            # continue previous work
            with open(self.saved_messages_path, "r") as fp:
                messages = loads(json.load(fp))
            messages = [self.system_message] + messages

        inputs = {"messages": messages}
        self.manager.invoke(inputs, {"recursion_limit": 1000})


if __name__ == "__main__":
    manager_instance = Manager()
    manager_instance.run()
