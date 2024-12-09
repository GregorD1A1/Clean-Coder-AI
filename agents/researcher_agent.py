from langchain_openai.chat_models import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama
from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph
from dotenv import load_dotenv, find_dotenv
from langchain.tools import tool
from tools.tools_coder_pipeline import (
     prepare_see_file_tool, prepare_list_dir_tool, retrieve_files_by_semantic_query
)
from tools.rag.retrieval import vdb_available
from utilities.util_functions import find_tools_json, list_directory_tree, render_tools
from utilities.langgraph_common_functions import (
    call_model, call_tool, ask_human, after_ask_human_condition, bad_json_format_msg, no_json_msg, finish_too_early_msg
)
from utilities.print_formatters import print_formatted, print_error
from utilities.llms import llm_open_router
import os


load_dotenv(find_dotenv())
mistral_api_key = os.getenv("MISTRAL_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
work_dir = os.getenv("WORK_DIR")


@tool
def final_response_researcher(files_to_work_on, reference_files, template_images):
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

llms = []
if anthropic_api_key:
    llms.append(ChatAnthropic(model='claude-3-5-sonnet-20241022', temperature=0.2, timeout=60).with_config({"run_name": "Researcher"}))
if os.getenv("OPENROUTER_API_KEY"):
    llms.append(llm_open_router("anthropic/claude-3.5-sonnet").with_config({"run_name": "Researcher"}))
if openai_api_key:
    llms.append(ChatOpenAI(model="gpt-4o", temperature=0.2, timeout=60).with_config({"run_name": "Researcher"}))
if os.getenv("OLLAMA_MODEL"):
    llms.append(ChatOllama(model=os.getenv("OLLAMA_MODEL")).with_config({"run_name": "Researcher"}))


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]


parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
with open(f"{parent_dir}/prompts/researcher_system.prompt", "r") as f:
    system_prompt_template = f.read()


# node functions
def call_model_researcher(state):
    state = call_model(state, llms)
    last_message = state["messages"][-1]
    if hasattr(last_message, 'json5_tool_calls') and len(last_message.json5_tool_calls) > 1:
        # Filter out the tool call with "final_response_researcher"
        state["messages"][-1].json5_tool_calls = [
            tool_call for tool_call in last_message.json5_tool_calls
            if tool_call["tool"] != "final_response_researcher"
        ]
    return state


# Logic for conditional edges
def after_agent_condition(state):
    last_message = state["messages"][-1]

    if last_message.content in (bad_json_format_msg, no_json_msg, finish_too_early_msg):
        return "agent"
    elif last_message.json5_tool_calls[0]["tool"] == "final_response_researcher":
        return "human"
    else:
        return "tool"


class Researcher():
    def __init__(self, work_dir):
        see_file = prepare_see_file_tool(work_dir)
        list_dir = prepare_list_dir_tool(work_dir)
        self.tools = [see_file, list_dir, final_response_researcher]
        if vdb_available():
            self.tools.append(retrieve_files_by_semantic_query)
        self.rendered_tools = render_tools(self.tools)

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
        return call_tool(state, self.tools)


    # just functions
    def research_task(self, task):
        print_formatted("Researcher starting its work", color="green")
        print_formatted("👋 Hey! I'm looking for a files on which we will work on together!", color="light_blue")

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
