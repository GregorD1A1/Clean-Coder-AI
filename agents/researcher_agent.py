import json

from langchain_openai.chat_models import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_community.chat_models import ChatOllama
from langchain_community.llms import Replicate
from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph import StateGraph
from dotenv import load_dotenv, find_dotenv
from langchain.tools import tool
from tools.tools_coder_pipeline import (
     prepare_see_file_tool, retrieve_files_by_semantic_query
)
from rag.retrieval import vdb_available
from utilities.util_functions import find_tools_json, list_directory_tree, render_tools
from utilities.langgraph_common_functions import (
    call_model, call_tool, ask_human, after_ask_human_condition, bad_json_format_msg, multiple_jsons_msg, no_json_msg
)
import os


load_dotenv(find_dotenv())
mistral_api_key = os.getenv("MISTRAL_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
work_dir = os.getenv("WORK_DIR")


@tool
def final_response(files_to_work_on, reference_files, template_images):
    """That tool outputs list of files programmer will need to change and paths to graphical patterns if some.
    Use that tool only when you 100% sure you found all the files programmer will need to modify.
    If not, do additional research. Include only the files you convinced will be useful.
    Provide only existing files, do not provide files to be implemented.

    tool input:
    :param files_to_work_on: ["List", "of", "existing files", "to potentially introduce", "changes"],
    :param reference_files: ["List", "of code files", "useful to code reference", "without images],
    :param template_images: ["List of", "template", "images"],
    """
    pass

#llm = ChatOllama(model="gemma2:9b-instruct-fp16")
#llm = ChatMistralAI(api_key=mistral_api_key, model="mistral-large-latest")
#llm = Replicate(model="meta/meta-llama-3.1-405b-instruct")
llms = []
if os.getenv("MISTRAL_API_KEY"):
    llms.append(ChatMistralAI(model="ministral-8b-latest").with_config({"run_name": "Researcher"}))
if anthropic_api_key:
    llms.append(ChatAnthropic(model='claude-3-5-sonnet-20240620', temperature=0.2, timeout=120).with_config({"run_name": "Researcher"}))
if openai_api_key:
    llms.append(ChatOpenAI(model="gpt-4o", temperature=0.2, timeout=120).with_config({"run_name": "Researcher"}))

class AgentState(TypedDict):
    messages: Sequence[BaseMessage]


parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
with open(f"{parent_dir}/prompts/researcher_system.prompt", "r") as f:
    system_prompt_template = f.read()


# node functions
def call_model_researcher(state):
    state = call_model(state, llms)
    return state


# Logic for conditional edges
def after_agent_condition(state):
    last_message = state["messages"][-1]

    if last_message.content in (bad_json_format_msg, multiple_jsons_msg, no_json_msg):
        return "agent"
    elif last_message.json5_tool_calls[0]["tool"] == "final_response":
        return "human"
    else:
        return "tool"


class Researcher():
    def __init__(self, work_dir):
        see_file = prepare_see_file_tool(work_dir)
        tools = [see_file, final_response]
        if vdb_available():
            tools.append(retrieve_files_by_semantic_query)
        self.rendered_tools = render_tools(tools)
        self.tool_executor = ToolExecutor(tools)

        # workflow definition
        researcher_workflow = StateGraph(AgentState)

        researcher_workflow.add_node("agent", call_model_researcher)
        researcher_workflow.add_node("tool", self.call_tool_researcher)
        researcher_workflow.add_node("human", ask_human)

        researcher_workflow.set_entry_point("agent")

        researcher_workflow.add_conditional_edges("agent", after_agent_condition)
        researcher_workflow.add_conditional_edges("human", after_ask_human_condition )
        researcher_workflow.add_edge("tool", "agent")

        self.researcher = researcher_workflow.compile()

    # node functions
    def call_tool_researcher(self, state):
        return call_tool(state, self.tool_executor)

    # just functions
    def research_task(self, task):
        print("Researcher starting its work")
        system_message = system_prompt_template.format(task=task, tools=self.rendered_tools)
        inputs = {
            "messages": [SystemMessage(content=system_message), HumanMessage(content=list_directory_tree(work_dir))]}
        researcher_response = self.researcher.invoke(inputs, {"recursion_limit": 100})["messages"][-2]

        tool_json = find_tools_json(researcher_response.content)[0]
        text_files = set(tool_json["tool_input"]["files_to_work_on"] + tool_json["tool_input"]["reference_files"])
        image_paths = tool_json["tool_input"]["template_images"]

        return text_files, image_paths


if __name__ == "__main__":
    task = """Check all system"""
    researcher = Researcher(work_dir)
    researcher.research_task(task)
