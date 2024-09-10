from langchain_openai.chat_models import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.llms import Replicate
from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph import StateGraph
from dotenv import load_dotenv, find_dotenv
from langchain.tools.render import render_text_description
from tools.tools_project_manager import add_task, modify_task, delete_task, finish_project_planning, reorder_tasks
from tools.tools_coder_pipeline import prepare_list_dir_tool, prepare_see_file_tool, ask_human_tool
from langchain_community.chat_models import ChatOllama
from utilities.util_functions import read_project_description, read_progress_description, get_project_tasks
from utilities.langgraph_common_functions import (call_model, call_tool, bad_json_format_msg, multiple_jsons_msg,
                                                  no_json_msg)
import os
import time


load_dotenv(find_dotenv())
work_dir = os.getenv("WORK_DIR")
list_dir = prepare_list_dir_tool(work_dir)
see_file = prepare_see_file_tool(work_dir)
tools = [
    add_task,
    modify_task,
    delete_task,
    reorder_tasks,
    list_dir,
    see_file,
    ask_human_tool,
    finish_project_planning,
]
rendered_tools = render_text_description(tools)

llm = ChatOpenAI(model="gpt-4o", temperature=0.4).with_config({"run_name": "Manager"})
#llm = ChatAnthropic(model='claude-3-5-sonnet-20240620', temperature=0.4).with_config({"run_name": "Manager"})
#llm = Replicate(model="meta/meta-llama-3.1-405b-instruct").with_config({"run_name": "Manager"})


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]


project_description = read_project_description()
tool_executor = ToolExecutor(tools)
tasks_progress_template = """Current project tasks:
{tasks}

What have been done so far:
{progress_description}"""

current_dir = os.path.dirname(os.path.realpath(__file__))
with open(f"{current_dir}/agents/prompts/manager_system.prompt", "r") as f:
    system_prompt_template = f.read()

system_message = SystemMessage(
    content=system_prompt_template.format(project_description=project_description, tools=rendered_tools)
)


# node functions
def call_model_manager(state):
    state = call_model(state, llm)
    state = cut_off_context(state)
    return state


def call_tool_manager(state):
    state = call_tool(state, tool_executor)
    state = actualize_tasks_list_and_progress_description(state)
    return state


# Logic for conditional edges
def after_agent_condition(state):
    last_message = state["messages"][-1]

    if last_message.content in (bad_json_format_msg, multiple_jsons_msg, no_json_msg):
        return "agent"
    else:
        return "tool"


# just functions
def actualize_tasks_list_and_progress_description(state):
    # Remove old tasks message
    state["messages"] = [msg for msg in state["messages"] if not hasattr(msg, "tasks_and_progress_message")]
    # Add new message
    project_tasks = get_project_tasks()
    progress_description = read_progress_description()
    tasks_and_progress_msg = HumanMessage(
        content=tasks_progress_template.format(tasks=project_tasks, progress_description=progress_description),
        tasks_and_progress_message=True
    )
    state["messages"].append(tasks_and_progress_msg)
    return state


def cut_off_context(state):
    system_message = next((msg for msg in state["messages"] if msg.type == "system"), None)
    last_messages_excluding_system = [msg for msg in state["messages"][-20:] if msg.type != "system"]
    state["messages"] = [system_message] + last_messages_excluding_system
    return state

# workflow definition
manager_workflow = StateGraph(AgentState)
manager_workflow.add_node("agent", call_model_manager)
manager_workflow.add_node("tool", call_tool_manager)
manager_workflow.set_entry_point("agent")
manager_workflow.add_conditional_edges("agent", after_agent_condition)
manager_workflow.add_edge("tool", "agent")
manager = manager_workflow.compile()


def run_manager():
    print("Manager starting its work")
    project_tasks = get_project_tasks()
    progress_description = read_progress_description()
    tasks_and_progress_msg = HumanMessage(
        content=tasks_progress_template.format(tasks=project_tasks, progress_description=progress_description),
        tasks_and_progress_message=True
    )
    start_human_message = HumanMessage(content="Go")    # Claude needs to have human message always as first
    inputs = {"messages": [system_message, tasks_and_progress_msg, start_human_message]}
    manager.invoke(inputs, {"recursion_limit": 1000})


if __name__ == "__main__":
    run_manager()
