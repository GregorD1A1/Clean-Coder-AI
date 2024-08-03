from langchain_openai.chat_models import ChatOpenAI
from langchain_community.llms import Replicate
from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph import StateGraph
from dotenv import load_dotenv, find_dotenv
from langchain.tools.render import render_text_description
from tools.tools_project_manager import (get_project_tasks, add_task, modify_task, delete_task, mark_task_as_done,
                                         ask_programmer_to_execute_task)
from tools.tools import list_dir, see_file, ask_human_tool
from utilities.util_functions import check_file_contents, find_tool_json, print_wrapped, read_project_description
from utilities.langgraph_common_functions import call_model, call_tool, ask_human, after_ask_human_condition
from langgraph.prebuilt import ToolNode


load_dotenv(find_dotenv())
tools = [
    get_project_tasks,
    add_task,
    modify_task,
    delete_task,
    mark_task_as_done,
    ask_programmer_to_execute_task,
    list_dir,
    see_file,
    ask_human_tool,
]
rendered_tools = render_text_description(tools)

llm = ChatOpenAI(model="gpt-4o", temperature=0.4).with_config({"run_name": "Manager"})
#llm = Replicate(model="meta/meta-llama-3.1-405b-instruct").with_config({"run_name": "Manager"})


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]


bad_json_format_msg = ("Bad json format. Json should contain fields 'tool' and 'tool_input' "
                       "and enclosed with '```json', '```' tags.")

project_description = read_project_description()
tool_executor = ToolExecutor(tools)

system_message = SystemMessage(content=f"""
You are project manager that guides programmer in his work, plan future tasks, checks quality of their execution and 
replans over and over (if needed) until project is finished.

Remember to mark tasks as done after they finished and remove when not needed.

Think and plan carefully before asking programmer to implement new features. Do not hesitate to write long reasonings 
before choosing an action - you are brain worker. Make sure task list is actual before 
choosing a task programmer need to work on. You can see project files by yourself to be able to define tasks more 
precisely. Before starting doing new task think, if it could be divided to smaller tasks.

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


def call_tool_researcher(state):
    return call_tool(state, tool_executor)


tool_node = ToolNode(tools)


# Logic for conditional edges
def after_agent_condition(state):
    last_message = state["messages"][-1]

    if last_message.content == bad_json_format_msg:
        return "agent"
    elif last_message.tool_call["tool"] == "final_response":
        return "human"
    else:
        return "tool"


# workflow definition
researcher_workflow = StateGraph(AgentState)

researcher_workflow.add_node("agent", call_model_manager)
researcher_workflow.add_node("tool", call_tool_researcher)
researcher_workflow.add_node("human", ask_human)

researcher_workflow.set_entry_point("agent")

researcher_workflow.add_conditional_edges(
    "agent",
    after_agent_condition,
)
researcher_workflow.add_conditional_edges(
    "human",
    after_ask_human_condition,
)
researcher_workflow.add_edge("tool", "agent")


researcher = researcher_workflow.compile()


def research_task():
    print("Manager starting its work")
    inputs = {"messages": [system_message, HumanMessage(content="Go")]}
    researcher_response = researcher.invoke(inputs, {"recursion_limit": 200})["messages"][-2]

if __name__ == "__main__":
    research_task()
