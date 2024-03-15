import os
import re
import json
from langgraph_coder.tools.tools import list_dir, see_file
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


load_dotenv(find_dotenv())
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")


@tool
def final_response(reasoning, files_for_executor):
    """Final response containing list of files executor will need to change. Use that tool only when you 100% sure
    you found all the files Executor will need to modify. If not, do additional research.
    :param reasoning: str, Reasoning what files will be needed.
    :param files_for_executor: List[str], List of files."""
    print("Files to change: ", files_for_executor)


tools = [list_dir, see_file, final_response]
rendered_tools = render_text_description(tools)

llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.2)
#llm = ChatOllama(model="mixtral") #, temperature=0)
#llm = PerplexityAILLM(model_name="mixtral-8x7b-instruct", temperature=0, api_key=PERPLEXITY_API_KEY)


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


tool_executor = ToolExecutor(tools)
system_message = SystemMessage(
        content="You are expert in filesystem research and in choosing right files. Your research is very careful, "
                "you always choosing only needed files, while leaving that not needed. "
                "You are helping your friend Executor to make provided task. "
                "Do filesystem research and provide existing files that executor will need to change or take a look at "
                "in order to do his task. NEVER recommend file you haven't seen yet. "
                "Never recommend files that not exist but need to be created."
                "Start your research from '/' dir."
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
    messages = state["messages"] + [system_message]
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
    human_response = input("Write 'ok' if you agree with a reserached files or provide commentary.")
    if human_response == "ok":
        return {"messages": [HumanMessage(content="Approved by human")]}
    else:
        return {"messages": [HumanMessage(content=human_response)]}


# Logic for conditional edges
def after_agent_condition(state):
    last_message = state["messages"][-1]
    print("last_message", last_message)

    if last_message.tool_call["tool"] == "final_response":
        return "end"
    else:
        return "continue"


def after_ask_human_condition(state):
    last_message = state["messages"][-1]

    if last_message.content == "Approved by human":
        return "end"
    else:
        return "return"


# workflow definition
researcher_workflow = StateGraph(AgentState)

researcher_workflow.add_node("agent", call_model)
researcher_workflow.add_node("tool", call_tool)
researcher_workflow.add_node("human", ask_human)

researcher_workflow.set_entry_point("agent")

researcher_workflow.add_conditional_edges(
    "agent",
    after_agent_condition,
    {
        "continue": "tool",
        "end": "human",
    },
)
researcher_workflow.add_conditional_edges(
    "human",
    after_ask_human_condition,
    {
        "end": END,
        "return": "agent"
    })
researcher_workflow.add_edge("tool", "agent")

researcher = researcher_workflow.compile()


def research_task(task):
    print("Researcher starting its work")
    inputs = {"messages": [HumanMessage(content=f"task: {task}")]}
    # try mx_iterations instead of recursion_limit
    researcher_response = researcher.invoke(inputs, {"recursion_limit": 50})["messages"][-2]
    files = find_tool_json(researcher_response.content)["tool_input"]["files_for_executor"]

    return files
