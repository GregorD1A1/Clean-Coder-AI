import os
import re
import json
from langchain_openai.chat_models import ChatOpenAI
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
import operator
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph import END, StateGraph
from dotenv import load_dotenv, find_dotenv
from langgraph.prebuilt import ToolInvocation
from langchain.tools.render import render_text_description
from langchain.tools import tool
from langchain_community.chat_models import ChatOllama
from tools.tools import list_dir, see_file, see_image
from utilities.util_functions import check_file_contents, find_tool_json, print_wrapped
from utilities.langgraph_common_functions import ask_human


load_dotenv(find_dotenv())


@tool
def final_response(reasoning, files_for_executor):
    """That tool outputs list of files executor will need to change and paths to graphical patterns if some.
    Use that tool only when you 100% sure you found all the files Executor will need to modify.
    If not, do additional research.
    'tool_input': {
        "reasoning": "Reasoning what files will be needed.",
        "files_to_work_on": ["List", "of", "files."],
        "template_images": ["List of image paths", "that be used as graphical patterns."]
    }
    """
    pass


tools = [list_dir, see_file, final_response]
rendered_tools = render_text_description(tools)

llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.2)
#llm = ChatOllama(model="openchat") #, temperature=0)


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

additional_knowledge = "Mostly files you interested in could be found in src/components/."

tool_executor = ToolExecutor(tools)
system_message = SystemMessage(
        content="You are expert in filesystem research and choosing right files."
                "Your research is very careful - rather check more files then less. If you not if you need to check some file or not - you check it. "
                "Good practice you follow is when found important dependencies that point from file you checking to "
                "other file, you check other file also. "
                "At your final response, you choosing only needed files, while leaving that not needed. "
                "You are helping your friend Executor to make provided task. "
                "Do filesystem research and provide existing files that executor will need to change or take a look at "
                "in order to do his task. NEVER recommend file you haven't seen yet. "
                "Never recommend files that not exist but need to be created."
                "Start your research from '/' dir."
                "Additional knowledge:\n"
                f"{additional_knowledge}\n\n"
                "\n\n"
                "You have access to following tools:\n"
                f"{rendered_tools}"
                "\n\n"
                "Generate response using next json blob (strictly follow it!): "
                "```json"
                "{"
                " 'tool': '$TOOL_NAME',"
                " 'tool_input': '$TOOL_PARAMS',"
                "}"
                "```"
    )


# node functions
def call_model(state):
    messages = state["messages"] + [system_message]
    response = llm.invoke(messages)
    tool_call = find_tool_json(response.content)
    response.tool_call = tool_call
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


def call_tool(state):
    last_message = state["messages"][-1]
    if not hasattr(last_message, "tool_call"):
        return {"messages": ["no tool called"]}
    tool_call = last_message.tool_call
    response = tool_executor.invoke(ToolInvocation(**tool_call))
    response_message = HumanMessage(content=str(response))

    return {"messages": [response_message]}


# Logic for conditional edges
def after_agent_condition(state):
    last_message = state["messages"][-1]

    if last_message.tool_call["tool"] == "final_response":
        return "human"
    else:
        return "tool"


def after_ask_human_condition(state):
    last_message = state["messages"][-1]

    if last_message.content == "Approved by human":
        return END
    else:
        return "agent"


# workflow definition
researcher_workflow = StateGraph(AgentState)

researcher_workflow.add_node("agent", call_model)
researcher_workflow.add_node("tool", call_tool)
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


def research_task(task):
    print("Researcher starting its work")
    inputs = {"messages": [HumanMessage(content=f"task: {task}")]}
    researcher_response = researcher.invoke(inputs, {"recursion_limit": 100})["messages"][-2]

    tool_json = find_tool_json(researcher_response.content)
    text_files = tool_json["tool_input"]["files_to_work_on"]
    file_contents = check_file_contents(text_files)

    image_paths = tool_json["tool_input"]["template_images"]
    images = []
    for image_path in image_paths:
        images.append(
            {
                "type": "text",
                "text": image_path,
            }
        )
        images.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{see_image(image_path)}",
                },
            }
        )
        '''
        images.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": see_image(image_path),
                },
            }
        )
        '''

    message_content = [f"task: {task},\n\n files: {file_contents}"] + images
    message_for_planner = HumanMessage(content=message_content)

    return message_for_planner, text_files, file_contents