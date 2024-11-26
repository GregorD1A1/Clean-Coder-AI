from langchain_openai.chat_models import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama
from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv, find_dotenv
from langchain.tools import tool
from tools.tools_coder_pipeline import (
     prepare_see_file_tool, prepare_list_dir_tool, retrieve_files_by_semantic_query
)
from tools.rag.retrieval import vdb_available
from utilities.util_functions import find_tools_json, list_directory_tree, render_tools
from utilities.langgraph_common_functions import (
    call_model, call_tool, bad_json_format_msg, finish_too_early_msg, no_json_msg
)
from utilities.llms import llm_open_router
import os


load_dotenv(find_dotenv())
mistral_api_key = os.getenv("MISTRAL_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
work_dir = os.getenv("WORK_DIR")


@tool
def final_response_file_answerer(answer, additional_materials):
    """Call that tool when you have answer for a provided questions or you sure you can't find an answer.

    tool input:
    :param answer: Provide answer(s) to question(s) here
    :param additional_materials: (Optional) You can provide code snippets here from files you seen to support your answer.
    """
    pass

#llm = ChatOllama(model="gemma2:9b-instruct-fp16")
#llm = ChatMistralAI(api_key=mistral_api_key, model="mistral-large-latest")
#llm = Replicate(model="meta/meta-llama-3.1-405b-instruct")
llms = []
if anthropic_api_key:
    llms.append(ChatAnthropic(model='claude-3-5-sonnet-20241022', temperature=0.2, timeout=120).with_config({"run_name": "File Answerer"}))
if os.getenv("OPENROUTER_API_KEY"):
    llms.append(llm_open_router("anthropic/claude-3.5-sonnet").with_config({"run_name": "File Answerer"}))
if openai_api_key:
    llms.append(ChatOpenAI(model="gpt-4o", temperature=0.2, timeout=120).with_config({"run_name": "File Answerer"}))
if os.getenv("OLLAMA_MODEL"):
    llms.append(ChatOllama(model=os.getenv("OLLAMA_MODEL")).with_config({"run_name": "File Answerer"}))


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]


parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
with open(f"{parent_dir}/prompts/researcher_file_answerer.prompt", "r") as f:
    system_prompt_template = f.read()


# node functions
def call_model_researcher(state):
    state = call_model(state, llms, printing=False)
    last_message = state["messages"][-1]
    if len(last_message.json5_tool_calls) > 1 and any(
            tool_call["tool"] == "final_response_file_answerer" for tool_call in last_message.json5_tool_calls):
        state["messages"].append(
            HumanMessage(content=finish_too_early_msg))
    return state


# Logic for conditional edges
def after_agent_condition(state):
    last_message = state["messages"][-1]

    if last_message.content in (bad_json_format_msg, finish_too_early_msg, no_json_msg):
        return "agent"
    elif last_message.json5_tool_calls[0]["tool"] == "final_response_file_answerer":
        return END
    else:
        return "tool"


class ResearchFileAnswerer():
    def __init__(self, work_dir):
        see_file = prepare_see_file_tool(work_dir)
        list_dir = prepare_list_dir_tool(work_dir)
        tools = [see_file, list_dir, final_response_file_answerer]
        if vdb_available():
            tools.append(retrieve_files_by_semantic_query)
        self.rendered_tools = render_tools(tools)
        self.tool_executor = ToolExecutor(tools)

        # workflow definition
        researcher_workflow = StateGraph(AgentState)

        researcher_workflow.add_node("agent", call_model_researcher)
        researcher_workflow.add_node("tool", self.call_tool_researcher)

        researcher_workflow.set_entry_point("agent")

        researcher_workflow.add_conditional_edges("agent", after_agent_condition)
        researcher_workflow.add_edge("tool", "agent")

        self.researcher = researcher_workflow.compile()

    # node functions
    def call_tool_researcher(self, state):
        return call_tool(state, self.tool_executor)

    # just functions
    def research_and_answer(self, questions):
        system_message = system_prompt_template.format(questions=questions, tools=self.rendered_tools)
        inputs = {
            "messages": [SystemMessage(content=system_message), HumanMessage(content=list_directory_tree(work_dir))]}
        researcher_response = self.researcher.invoke(inputs, {"recursion_limit": 100})["messages"][-1]
        tool_json = find_tools_json(researcher_response.content)[0]
        answer = tool_json["tool_input"]

        return answer


if __name__ == "__main__":
    questions = """What is the name of jokes endpoint?"""
    researcher = ResearchFileAnswerer(work_dir)
    researcher.research_and_answer(questions)
