from langchain_openai.chat_models import ChatOpenAI
from langchain_community.llms import Replicate
from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph import StateGraph
from dotenv import load_dotenv, find_dotenv
from langchain.tools.render import render_text_description
from tools.tools_project_manager import add_task, modify_task, delete_task, finish_project_planning, reorder_tasks
from tools.tools_coder_pipeline import list_dir, see_file, ask_human_tool
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from utilities.util_functions import print_wrapped, read_project_description, get_project_tasks
from utilities.langgraph_common_functions import (call_model, call_tool, bad_json_format_msg, multiple_jsons_msg,
                                                  no_json_msg, ask_human)
from langgraph.prebuilt import ToolNode


load_dotenv(find_dotenv())
tavily_api_wrapper = TavilySearchAPIWrapper()
internet_research = TavilySearchResults(api_wrapper=tavily_api_wrapper)
tools = [
    add_task,
    modify_task,
    delete_task,
    reorder_tasks,
    list_dir,
    see_file,
    internet_research,
    ask_human_tool,
    finish_project_planning,
]
rendered_tools = render_text_description(tools)

llm = ChatOpenAI(model="gpt-4o", temperature=0.4).with_config({"run_name": "Manager"})
#llm = Replicate(model="meta/meta-llama-3.1-405b-instruct").with_config({"run_name": "Manager"})


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]


project_description = read_project_description()
tool_executor = ToolExecutor(tools)

system_message = SystemMessage(content=f"""
You are project manager that plans future tasks for programmer. You need to plan the work task by task in proper order.
When you unsure how some feature need to be implemented, you doing internet research or asking human.

Think and plan carefully. Do not hesitate to write long reasoning before choosing an action - you are brain worker. 
You can see project files by yourself to be able to define tasks more project content related. 

Here is description of the project you work on:
{project_description}

You have access to following tools:
{rendered_tools}\n
First, provide step by step reasoning about what do you need to find in order to accomplish the task. Ensure, you have
long and thoughtful reasoning before every tool call. Remember, you are brain worker.
Next, generate response using json template: Choose only one tool to use.
```json
{{
    "tool": "$TOOL_NAME",
    "tool_input": "$TOOL_PARAMS",
}}
```
"""
)


# node functions
def call_model_manager(state):
    state, response = call_model(state, llm)
    # safety mechanism for a bad json
    tool_call = response.tool_call
    if tool_call is None or "tool" not in tool_call:
        state["messages"].append(HumanMessage(content=bad_json_format_msg))
    return state


def call_tool_manager(state):
    state = call_tool(state, tool_executor)
    state = exchange_tasks_list(state)
    return state


tool_node = ToolNode(tools)


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
    state["messages"].append(file_contents_msg)
    return state


# workflow definition
manager_workflow = StateGraph(AgentState)

manager_workflow.add_node("agent", call_model_manager)
manager_workflow.add_node("tool", call_tool_manager)

manager_workflow.set_entry_point("agent")

manager_workflow.add_conditional_edges(
    "agent",
    after_agent_condition,
)
manager_workflow.add_edge("tool", "agent")


manager = manager_workflow.compile()


def run_manager():
    print("Manager starting its work")
    project_tasks = get_project_tasks()
    inputs = {"messages": [system_message, HumanMessage(content=project_tasks, project_tasks_message=True)]}
    manager.invoke(inputs, {"recursion_limit": 200})["messages"][-2]

if __name__ == "__main__":
    run_manager()
