import os
from tools.tools_coder_pipeline import (
    ask_human_tool, prepare_create_file_tool, prepare_replace_code_tool, prepare_insert_code_tool
)
from langchain_openai.chat_models import ChatOpenAI
from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv, find_dotenv
from langchain.tools import tool
from langchain_community.chat_models import ChatOllama
from langchain_anthropic import ChatAnthropic
from utilities.llms import llm_open_router
from utilities.print_formatters import print_formatted, print_error
from utilities.util_functions import (
    check_file_contents, render_tools, find_tools_json, exchange_file_contents, bad_tool_call_looped
)
from utilities.langgraph_common_functions import (
    call_model, call_tool, bad_json_format_msg, multiple_jsons_msg, no_json_msg, agent_looped_human_help
)


load_dotenv(find_dotenv())
log_file_path = os.getenv("LOG_FILE")
frontend_port = os.getenv("FRONTEND_PORT")


@tool
def final_response_executor(test_instruction):
    """Call that tool when all plan steps are implemented to finish your job.
tool input:
:param test_instruction: write detailed instruction for human what actions he need to do in order to check if
implemented changes work correctly."""
    print_formatted(content=test_instruction, color="blue")


# llm = ChatTogether(model="meta-llama/Llama-3-70b-chat-hf", temperature=0).with_config({"run_name": "Executor"})
# llm = ChatOllama(model="mixtral"), temperature=0).with_config({"run_name": "Executor"})
llms = []
if os.getenv("ANTHROPIC_API_KEY"):
    llms.append(ChatAnthropic(
        model='claude-3-5-sonnet-20240620', temperature=0, max_tokens=2000, timeout=60
    ).with_config({"run_name": "Executor"}))
if os.getenv("OPENROUTER_API_KEY"):
    llms.append(llm_open_router("anthropic/claude-3.5-sonnet").with_config({"run_name": "Executor"}))
if os.getenv("OPENAI_API_KEY"):
    llms.append(ChatOpenAI(model="gpt-4o", temperature=0, timeout=60).with_config({"run_name": "Executor"}))
if os.getenv("OLLAMA_MODEL"):
    llms.append(ChatOllama(model=os.getenv("OLLAMA_MODEL")).with_config({"run_name": "Executor"}))


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]


parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

with open(f"{parent_dir}/prompts/executor_system.prompt", "r") as f:
    system_prompt_template = f.read()


class Executor():
    def __init__(self, files, work_dir):
        self.work_dir = work_dir
        self.tools = prepare_tools(work_dir)
        rendered_tools = render_tools(self.tools)
        self.system_message = SystemMessage(
            content=system_prompt_template.format(executor_tools=rendered_tools)
        )
        self.files = files

        # workflow definition
        executor_workflow = StateGraph(AgentState)

        executor_workflow.add_node("agent", self.call_model_executor)
        executor_workflow.add_node("tool", self.call_tool_executor)
        executor_workflow.add_node("human_help", agent_looped_human_help)

        executor_workflow.set_entry_point("agent")

        # executor_workflow.add_edge("agent", "checker")
        executor_workflow.add_edge("tool", "agent")
        executor_workflow.add_edge("human_help", "agent")
        executor_workflow.add_conditional_edges("agent", self.after_agent_condition)

        self.executor = executor_workflow.compile()

    # node functions
    def call_model_executor(self, state):
        state = call_model(state, llms)
        last_message = state["messages"][-1]
        if last_message.type == "ai" and len(last_message.json5_tool_calls) > 1:
            state["messages"].append(
                HumanMessage(content=multiple_jsons_msg))
            print_error("\nToo many jsons provided, asked to provide one.")
        return state

    def call_tool_executor(self, state):
        last_ai_message = state["messages"][-1]
        state = call_tool(state, self.tools)
        for tool_call in last_ai_message.json5_tool_calls:
            if tool_call["tool"] == "create_file_with_code":
                self.files.add(tool_call["tool_input"]["filename"])
        state = exchange_file_contents(state, self.files, self.work_dir)
        return state

    # Conditional edge functions
    def after_agent_condition(self, state):
        last_message = state["messages"][-1]

        if bad_tool_call_looped(state):
            return "human_help"
        elif last_message.content in (bad_json_format_msg, multiple_jsons_msg, no_json_msg):
            return "agent"
        elif last_message.json5_tool_calls[0]["tool"] == "final_response_executor":
            return END
        else:
            return "tool"

    # just functions
    def do_task(self, task, plan):
        print_formatted("Executor starting its work", color="green")
        print_formatted("✅ I follow the plan and will implement necessary changes!", color="light_blue")
        file_contents = check_file_contents(self.files, self.work_dir)
        inputs = {"messages": [
            self.system_message,
            HumanMessage(content=f"Task: {task}\n\n######\n\nPlan:\n\n{plan}"),
            HumanMessage(content=f"File contents: {file_contents}", contains_file_contents=True)
        ]}
        final_response = self.executor.invoke(inputs, {"recursion_limit": 150})
        test_instruction = find_tools_json(final_response['messages'][-1].content)[0]["tool_input"]

        return test_instruction, self.files


def prepare_tools(work_dir):
    replace_code = prepare_replace_code_tool(work_dir)
    insert_code = prepare_insert_code_tool(work_dir)
    create_file = prepare_create_file_tool(work_dir)
    tools = [replace_code, insert_code, create_file, ask_human_tool, final_response_executor]

    return tools
