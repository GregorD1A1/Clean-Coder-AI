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

current_dir = os.path.dirname(os.path.realpath(__file__))
with open(f"{current_dir}/agents/prompts/manager_system.prompt", "r") as f:
    system_prompt_template = f.read()

system_message = SystemMessage(
    content=system_prompt_template.format(project_description=project_description, tools=rendered_tools)
)


# node functions
def call_model_manager(state):
    state = call_model(state, llm)
    return state


def call_tool_manager(state):
    state = call_tool(state, tool_executor)
    state = exchange_tasks_list(state)
    if state["messages"][-2].tool_call["tool"] == "finish_project_planning":
        actualize_progress_description(state)
    return state


# Logic for conditional edges
def after_agent_condition(state):
    last_message = state["messages"][-1]

    if last_message.content in (bad_json_format_msg, multiple_jsons_msg, no_json_msg):
        return "agent"
    else:
        return "tool"


# just functions
def exchange_tasks_list(state):
    # Remove old tasks message
    state["messages"] = [msg for msg in state["messages"] if not hasattr(msg, "project_tasks_message")]
    # Add new message
    project_tasks = get_project_tasks()
    file_contents_msg = HumanMessage(content=project_tasks, project_tasks_message=True)
    state["messages"].insert(1, file_contents_msg)
    return state


def actualize_progress_description(state):
    # Remove old one
    state["messages"] = [msg for msg in state["messages"] if not hasattr(msg, "progress_description_message")]
    progress_description = read_progress_description()
    with open(os.path.join(work_dir, ".clean_coder", "manager_progress_description.txt"), "w") as f:
        f.write(progress_description)
    progress_msg = HumanMessage(content=
                                f"Here is description what been done so far in the project:\n{progress_description}",
                                progress_description_message=True
    )
    state["messages"].insert(2, progress_msg)


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
    progress_description_message = HumanMessage(
        content=f"Here is description what been done so far in the project:\n{read_progress_description()}",
        progress_description_message=True
    )
    inputs = {"messages": [system_message, HumanMessage(content=project_tasks, project_tasks_message=True), progress_description_message]}
    manager.invoke(inputs, {"recursion_limit": 1000})


if __name__ == "__main__":
    run_manager()
