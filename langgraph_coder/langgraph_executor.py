import os
import re
import json
from langgraph_coder.tools.tools import see_file, modify_code, insert_code, create_file_with_code, check_application_logs
from langchain_openai.chat_models import ChatOpenAI
from typing import TypedDict, Annotated, List, Sequence
from langchain_core.messages import BaseMessage
import operator
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph import END, StateGraph
from dotenv import load_dotenv, find_dotenv
from langgraph.prebuilt import ToolInvocation
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.tools.render import render_text_description
from langchain.tools import tool
from langchain_community.chat_models import ChatOllama
from langchain_anthropic import ChatAnthropic


load_dotenv(find_dotenv())


@tool
def final_response(are_you_sure):
    """Call that tool when all planned changes are implemented.
    :param are_you_sure: str, Write 'yes, I'm sure' if you absolutely sure all needed changes are done."""
    pass


tools = [see_file, modify_code, insert_code, create_file_with_code, final_response]
rendered_tools = render_text_description(tools)

llm = ChatOpenAI(model="gpt-4-turbo-preview", streaming=True)
#llm = ChatAnthropic(model='claude-3-opus-20240229')
#llm = ChatOllama(model="mixtral"), temperature=0)


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


tool_executor = ToolExecutor(tools)
system_message = SystemMessage(
        content="You are senior programmer. You need to improve existing code using provided tools. Introduce changes "
                "from plan one by one, means you can write only one json with change in that step."
                "You prefer to initiate your modifications from the higher line numbers within the code. "
                "This method prevents subsequent amendments from incorrectly overwriting the previously adjusted file."
                "\n\n"
                "You have access to following tools:\n"
                f"{rendered_tools}"
                "\n\n"
                "To use tool, strictly follow json blob:"
                "```json"
                "{"
                " 'tool': '$TOOL_NAME',"
                " 'tool_input': '$TOOL_PARAMETERS',"
                "}"
                "```"
    )


def find_tool_json(response):
    match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)

    if match:
        json_str = match.group(1).strip()
        print("Tool call: ", json_str)
        json_obj = json.loads(json_str)
        return json_obj
    else:
        return None


# node functions
def call_model(state):
    messages = state["messages"]# + [system_message]
    response = llm.invoke(messages)
    tool_call_json = find_tool_json(response.content)
    response.tool_call = tool_call_json
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


def call_tool(state):
    last_message = state["messages"][-1]
    tool_call = last_message.tool_call
    response = tool_executor.invoke(ToolInvocation(**tool_call))
    response_message = HumanMessage(content=str(response), name=tool_call["tool"])

    return {"messages": [response_message]}


def ask_human(state):
    last_message = state["messages"][-1]

    human_response = input(last_message.content)
    if not human_response:
        return {"messages": [HumanMessage(content="Approved by human")]}
    else:
        return {"messages": [HumanMessage(content=human_response)]}


def check_logs(state):
    logs = check_application_logs()
    #logs = input("Write 'ok' to continue or paste logs of error (Use that feature only for backend).")
    if logs == "ok":
        return {"messages": [HumanMessage(content="Logs are healthy.")]}
    else:
        return {"messages": [HumanMessage(content=logs)]}


# Logic for conditional edges
def after_agent_condition(state):
    last_message = state["messages"][-1]

    #if not last_message.tool_call:
    #    return "human"
    if last_message.tool_call["tool"] == "final_response":
        return "end"
    else:
        return "continue"


def after_check_log_condition(state):
    last_message = state["messages"][-1]

    if last_message.content == "Logs are healthy.":
        return "end"
    else:
        return "return"

def after_ask_human_condition(state):
    last_message = state["messages"][-1]

    if last_message.content == "Approved by human":
        return "end"
    else:
        return "return"

# workflow definition
executor_workflow = StateGraph(AgentState)

executor_workflow.add_node("agent", call_model)
executor_workflow.add_node("tool", call_tool)
executor_workflow.add_node("check_log", check_logs)
executor_workflow.add_node("human", ask_human)

executor_workflow.set_entry_point("agent")

executor_workflow.add_conditional_edges(
    "agent",
    after_agent_condition,
    {
        "continue": "tool",
        #"human": "human",
        "end": "check_log",
    },
)
executor_workflow.add_conditional_edges(
    "check_log",
    after_check_log_condition,
    {
        "return": "agent",
        "end": "human",
    }
)
executor_workflow.add_conditional_edges(
    "human",
    after_ask_human_condition,
    {
        "return": "agent",
        "end": END,
    }
)
executor_workflow.add_edge("tool", "agent")

executor = executor_workflow.compile()


def do_task(task, plan, file_contents):
    print("Executor starting its work")
    inputs = {"messages": [system_message,HumanMessage(content=f"Task: {task}\n\nPlan: {plan}\n\nFile contents: {file_contents}")]}
    executor_response = executor.invoke(inputs, {"recursion_limit": 50})["messages"][-1]

if __name__ == "__main__":
    executor.get_graph().draw_png()
