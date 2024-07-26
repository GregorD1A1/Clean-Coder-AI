from langchain_openai.chat_models import ChatOpenAI
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_community.chat_models import ChatOllama
from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph import StateGraph
from dotenv import load_dotenv, find_dotenv
from langchain.tools.render import render_text_description
from tools.tools_project_manager import (get_project_tasks, add_task, modify_task, delete_task, mark_task_as_done,
                                         ask_programmer_to_execute_task, ask_tester_to_check_if_change_been_implemented_correctly)
from utilities.util_functions import check_file_contents, find_tool_xml, find_tool_json, print_wrapped, read_project_knowledge
from utilities.langgraph_common_functions import call_model, call_tool, ask_human, after_ask_human_condition
import os


load_dotenv(find_dotenv())
tools = [
    get_project_tasks,
    add_task,
    modify_task,
    delete_task,
    mark_task_as_done,
    ask_programmer_to_execute_task,
    ask_tester_to_check_if_change_been_implemented_correctly,
]
rendered_tools = render_text_description(tools)

llm = ChatOpenAI(model="gpt-4o", temperature=0.4).with_config({"run_name": "Planer"})


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]


bad_json_format_msg = ("Bad json format. Json should contain fields 'tool' and 'tool_input' "
                       "and enclosed with '```json', '```' tags.")

project_description = read_project_knowledge()
tool_executor = ToolExecutor(tools)

project_description = """Backend for internet shop with skin bags.
"""

system_message = SystemMessage(content=f"""
You are project manager that guides programmer in his work, plan future tasks, checks quality of their execution and 
replans over and over (if needed) until project is finished.

Here is description of the project you work on:
{project_description}

You have access to following tools:
{rendered_tools}\n
First, provide step by step reasoning about what do you need to find in order to accomplish the task.
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
    researcher_response = researcher.invoke(inputs, {"recursion_limit": 100})["messages"][-2]

if __name__ == "__main__":
    research_task()
