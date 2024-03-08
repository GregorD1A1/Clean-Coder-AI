import os
import re
import json
from tools.tools_crew import list_dir, see_file
from langchain_openai.chat_models import ChatOpenAI
from langgraph_coder.perplexity_ai_llm import PerplexityAILLM
from typing import TypedDict, Annotated, List, Sequence
from langchain_core.messages import BaseMessage
import operator
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph import END, StateGraph
from dotenv import load_dotenv, find_dotenv
from langgraph.prebuilt import ToolInvocation
from langchain_core.messages import HumanMessage, SystemMessage, FunctionMessage
from langchain.tools.render import render_text_description, render_text_description_and_args
from langchain.tools import tool


load_dotenv(find_dotenv())
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")


@tool
def final_response(reasoning, files_for_executor):
    """Final response containing list of files executor will need to change. Use that tool only when you 100% sure
    you found all the files Executor will need to modify. If not, do additional research.
    :param reasoning: str, Reasoning what files will be needed.
    :param files_for_executor: List[str], List of files."""
    pass


tools = [list_dir, see_file, final_response]
rendered_tools = render_text_description(tools)

llm = ChatOpenAI(model="gpt-4-turbo-preview", streaming=True)
#llm = PerplexityAILLM(model_name="mixtral-8x7b-instruct", temperature=0, api_key=PERPLEXITY_API_KEY)


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


tool_executor = ToolExecutor(tools)
system_message = SystemMessage(
        content="You are expert in filesystem research and in choosing right files. Your research is very careful, "
                "you always choosing only needed files, while leaving that not needed. "
                "You are helping your friend Executor to make provided task. "
                "Do filesystem research and provide files that executor will need to change in order to do his "
                "task. Never recommend file you haven't seen yet."
                "\n\n"
                "You have access to following tools:\n"
                f"{rendered_tools}"
                "\n\n"
                "To use tool, use following json blob:"
                "```json"
                "{{"
                " 'tool': '$TOOL_NAME',"
                " 'tool_parameters': '$PARAS',"
                "}}"
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
    action = ToolInvocation(
        tool=tool_call["tool"],
        tool_input=tool_call["tool_parameters"]
    )
    response = tool_executor.invoke(action)
    # We use the response to create a FunctionMessage
    function_message = FunctionMessage(content=str(response), name=action.tool)
    # We return a list, because this will get added to the existing list
    return {"messages": [function_message]}


def ask_human(state):
    last_message = state["messages"][-1]

    human_response = input(last_message.content)
    if not human_response:
        return {"messages": [HumanMessage(content="Approved by human")]}
    else:
        return {"messages": [HumanMessage(content=human_response)]}


# Logic for conditional edges
def after_agent_condition(state):
    last_message = state["messages"][-1]
    print("last_message", last_message)

    if not last_message.tool_call:
        return "human"
    elif last_message.tool_call["tool"] == "final_response":
        return "end"
    else:
        return "continue"


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
        "human": "human",
        "end": END,
    },
)

researcher_workflow.add_edge("tool", "agent")
researcher_workflow.add_edge("human", "agent")

researcher = researcher_workflow.compile()

def research_task(task):
    print("Researcher starting its work")
    inputs = {"messages": [HumanMessage(content=f"task: {task}")]}
    researcher_response = researcher.invoke(inputs, {"recursion_limit": 50})["messages"][-1]
    files = find_tool_json(researcher_response.content)["tool_parameters"]["files_for_executor"]

    file_contents = str()
    for file_name in files:
        file_content = see_file(file_name)
        file_contents += "File: " + file_name + ":\n\n" + file_content + "\n\n###\n\n"

    return file_contents

if __name__ == "__main__":
    inputs = {"messages": [HumanMessage(content="task: Create an endpoint that saves new post without asking user")]}
    response = researcher.invoke(inputs)
    print(response)
    """
    for output in researcher.stream(inputs):
        # stream() yields dictionaries with output keyed by node name
        for key, value in output.items():
            print(f"Output from node '{key}':")
            print("---")
            print(value)
        print("\n---\n")
    """