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
from tools.tools_coder_pipeline import list_dir, see_file, ask_human_tool
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from langchain_community.chat_models import ChatOllama
from utilities.util_functions import print_wrapped, read_project_description, get_project_tasks, find_tool_json
from utilities.langgraph_common_functions import (call_model, call_tool, bad_json_format_msg, multiple_jsons_msg,
                                                  no_json_msg, ask_human)
import os


load_dotenv(find_dotenv())
work_dir = os.getenv("WORK_DIR")
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
#llm = ChatAnthropic(model='claude-3-5-sonnet-20240620', temperature=0.4).with_config({"run_name": "Manager"})
#llm = Replicate(model="meta/meta-llama-3.1-405b-instruct").with_config({"run_name": "Manager"})


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]


project_description = read_project_description()
tool_executor = ToolExecutor(tools)

system_message = SystemMessage(content=f"""
You are project manager that plans future tasks for programmer. You need to plan the work task by task in proper order.
When you unsure how some feature need to be implemented, you doing internet research or asking human.

Think and plan carefully. Write long reasoning before choosing an action - you are brain worker. 
You can see project files by yourself to be able to define tasks more project content related. 
Do not create/modify tasks without watching project files first. Do not add new tasks if you unsure if they are not done already.

Tasks you are creating are always very concrete, showing programmer how exactly and with which tools he can implement 
the change. If you unsure which technologies/resources to use, ask human before creating/modifying task.
Avoid creating flaky tasks, where it's unclear how to do task and if it is needed at all.

When you need to decide about introducing new technology into the project, consult it with human first. 

Here is description of the project you work on:
+++++
{project_description}
+++++

You have access to following tools:
{rendered_tools}\n
Never imagine tools or tool parameters that not provided above!

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


# Logic for conditional edges
def after_agent_condition(state):
    last_message = state["messages"][-1]

    if last_message.content in (bad_json_format_msg, multiple_jsons_msg, no_json_msg):
        return "agent"
    else:
        return "tool"


def after_tool_condition(state):
    if state["messages"][-2].tool_call["tool"] == "finish_project_planning":
        return "write_progress"
    else:
        return "agent"


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

    actualize_description_message = f"""After task been executed, actualize description of project progress. 
Write what have been done in the project so far in up to 7 sentences. Never imagine facts.

Previous progress description, before last task execution:
{progress_description}
Return json according template:
```json
{{
    "tool": "actualize_progress_description",
    "tool_input": {{
        "progress_description": "$PROGRESS_DESCRIPTION"
}},",
}}
```
"""
    print("Writing description of progress done.")
    messages = state["messages"]
    messages.append(HumanMessage(content=actualize_description_message))
    response = llm.invoke(messages)
    print(response.content)
    response_json = find_tool_json(response.content)
    progress_description = response_json["tool_input"]["progress_description"]
    print(progress_description)

    with open(os.path.join(work_dir, ".clean_coder", "manager_progress_description.txt"), "w") as f:
        f.write(progress_description)

    progress_msg = HumanMessage(content=
                                f"Here is description what been done so far in the project:\n{progress_description}",
                                progress_description_message=True
    )
    state["messages"].insert(2, progress_msg)



def read_progress_description():
    file_path = os.path.join(work_dir, ".clean_coder", "manager_progress_description.txt")
    if not os.path.exists(file_path):
        open(file_path, 'a').close()  # Creates file if it doesn't exist
        progress_description = "<empty>"
    else:
        with open(file_path, "r") as f:
            progress_description = f.read()
    return progress_description


# workflow definition
manager_workflow = StateGraph(AgentState)

manager_workflow.add_node("agent", call_model_manager)
manager_workflow.add_node("tool", call_tool_manager)
manager_workflow.add_node("write_progress", actualize_progress_description)

manager_workflow.set_entry_point("agent")

manager_workflow.add_conditional_edges(
    "agent",
    after_agent_condition,
)
manager_workflow.add_conditional_edges(
    "tool",
    after_tool_condition,
)
manager_workflow.add_edge("write_progress", "agent")


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

    #state = AgentState(messages=[system_message, HumanMessage(content="Ok, start"), AIMessage(content="Task of creating profile name application been executed.")])
    #actualize_progress_description(state)
