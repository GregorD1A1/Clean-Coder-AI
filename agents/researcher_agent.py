from langchain_openai.chat_models import ChatOpenAI
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_community.chat_models import ChatOllama
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from llamaapi import LlamaAPI
from langchain_experimental.llms import ChatLlamaAPI
from langchain_anthropic import ChatAnthropic
from langchain_community.llms import Replicate
from langchain_groq import ChatGroq
from langchain_together import ChatTogether
from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph import StateGraph
from dotenv import load_dotenv, find_dotenv
from langchain.tools.render import render_text_description
from langchain.tools import tool
from tools.tools import list_dir, see_file, see_image, retrieve_files_by_semantic_query
from rag.retrieval import vdb_availabe
from utilities.util_functions import check_file_contents, find_tool_xml, find_tool_json, print_wrapped
from utilities.langgraph_common_functions import call_model, call_tool, ask_human, after_ask_human_condition
import os


load_dotenv(find_dotenv())
mistral_api_key = os.getenv("MISTRAL_API_KEY")


@tool
def final_response(files_to_work_on, reference_files, template_images):
    """That tool outputs list of files executor will need to change and paths to graphical patterns if some.
    Use that tool only when you 100% sure you found all the files Executor will need to modify.
    If not, do additional research. Include only the files you convinced will be useful.
    Provide only existing files.

    tool input:
    :param files_to_work_on: ["List", "of", "existing files", "to potentially introduce", "changes"],
    :param reference_files: ["List", "of code files", "useful to code reference", "without images],
    :param template_images: ["List of", "template", "images"],
    """
    pass


tools = [list_dir, see_file, final_response]
if vdb_availabe:
    tools.append(retrieve_files_by_semantic_query)
rendered_tools = render_text_description(tools)

#stop_sequence = "\n```\n"
stop_sequence = None

#llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
llm = ChatAnthropic(model='claude-3-5-sonnet-20240620', temperature=0.2)
#llm = ChatGroq(model="llama3-70b-8192", temperature=0.3).with_config({"run_name": "Researcher"})
#llm = ChatOllama(model="llama3.1")
#llm = ChatMistralAI(api_key=mistral_api_key, model="mistral-large-latest")
#llm = ChatTogether(model="meta-llama/Llama-3-70b-chat-hf", temperature=0.3).with_config({"run_name": "Researcher"})
#llm = ChatNVIDIA(model="nvidia/llama3-chatqa-1.5-70b")
#llama = LlamaAPI(os.getenv("LLAMA_API_KEY"))
#llm = ChatLlamaAPI(client=llama)
'''llm = ChatOpenAI(
    model='deepseek-chat',
    openai_api_key='',
    openai_api_base='https://api.deepseek.com/v1',
    temperature=0.2
)'''
#llm = Replicate(model="meta/meta-llama-3.1-405b-instruct")


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]


bad_json_format_msg = ("Bad json format. Json should contain fields 'tool' and 'tool_input' "
                       "and enclosed with '```json', '```' tags.")

tool_executor = ToolExecutor(tools)
system_message_content = f"""As a curious filesystem researcher, examine files thoroughly, prioritizing comprehensive checks. 
You checking a lot of different folders looking around for interesting files (hey, you are very curious!) before giving the final answer.
The more folders/files you will check, the more they will pay you.
When you discover significant dependencies from one file to another, ensure to inspect both. 
Your final selection should include files needed to be modified or needed as reference for a programmer 
(for example to see how code in similar file implemented). 
Avoid recommending unseen or non-existent files in final response. Start from '/' directory.
You need to point out all files programmer needed to see to execute the task and only that task. Task is:
'''
{{task}}
'''
As a researcher, you are not allowed to make any code modifications. 

You have access to following tools:
{rendered_tools}

First, provide step by step reasoning about results of your previous action. Think what do you need to find now in order to accomplish the task.
Next, generate response using json template: Choose only one tool to use.
```json
{{{{
    "tool": "$TOOL_NAME",
    "tool_input": "$TOOL_PARAMS",
}}}}
```
"""


# node functions
def call_model_researcher(state):
    state, response = call_model(state, llm, stop_sequence_to_add=stop_sequence)
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

researcher_workflow.add_node("agent", call_model_researcher)
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


def research_task(task):
    print("Researcher starting its work")
    system_message = system_message_content.format(task=task)
    inputs = {"messages": [SystemMessage(content=system_message), HumanMessage(content=f"Go")]}
    researcher_response = researcher.invoke(inputs, {"recursion_limit": 100})["messages"][-2]

    #tool_json = find_tool_xml(researcher_response.content)
    tool_json = find_tool_json(researcher_response.content)
    text_files = set(tool_json["tool_input"]["files_to_work_on"] + tool_json["tool_input"]["reference_files"])
    file_contents = check_file_contents(text_files)

    image_paths = tool_json["tool_input"]["template_images"]
    images = [
                 {"type": "text", "text": image_path}
                 for image_path in image_paths
        ] + [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{see_image(image_path)}"}}
        for image_path in image_paths
    ]
    # images for claude
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

    return text_files, file_contents, images