import os
from tools.tools_coder_pipeline import (
    ask_human_tool, TOOL_NOT_EXECUTED_WORD, prepare_list_dir_tool, prepare_see_file_tool,
    prepare_create_file_tool, prepare_replace_code_tool, prepare_insert_code_tool, prepare_watch_web_page_tool
)
from langchain_openai.chat_models import ChatOpenAI
from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph import StateGraph
from dotenv import load_dotenv, find_dotenv
from langchain.tools import tool
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama
from langchain_anthropic import ChatAnthropic
from utilities.print_formatters import print_formatted
from utilities.util_functions import check_file_contents, check_application_logs, render_tools
from utilities.langgraph_common_functions import (
    call_model, call_tool, ask_human, after_ask_human_condition, bad_json_format_msg, multiple_jsons_msg, no_json_msg,
    agent_looped_human_help,
)
from utilities.user_input import user_input

load_dotenv(find_dotenv())
log_file_path = os.getenv("LOG_FILE")
frontend_port = os.getenv("FRONTEND_PORT")


@tool
def final_response(test_instruction):
    """Call that tool when all changes are implemented to tell the job is done.
tool input:
:param test_instruction: write detailed instruction for human what actions he need to do in order to check if
implemented changes work correctly."""
    print_formatted(test_instruction, color="blue")


# llm = ChatTogether(model="meta-llama/Llama-3-70b-chat-hf", temperature=0).with_config({"run_name": "Executor"})
# llm = ChatOllama(model="mixtral"), temperature=0).with_config({"run_name": "Executor"})
llms = []
if os.getenv("ANTHROPIC_API_KEY"):
    llms.append(
        ChatAnthropic(
            model='claude-3-5-sonnet-20241022', temperature=0, max_tokens=2000, timeout=120
        ).with_config({"run_name": "Debugger"})
    )
if os.getenv("OPENAI_API_KEY"):
    llms.append(ChatOpenAI(model="gpt-4o", temperature=0, timeout=120).with_config({"run_name": "Debugger"}))


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]


parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

with open(f"{parent_dir}/prompts/debugger_system.prompt", "r") as f:
    system_prompt_template = f.read()


class Debugger():
    def __init__(self, files, work_dir, human_feedback):
        self.work_dir = work_dir
        tools = prepare_tools(work_dir)
        rendered_tools = render_tools(tools)
        self.tool_executor = ToolExecutor(tools)
        self.system_message = SystemMessage(
            content=system_prompt_template.format(executor_tools=rendered_tools)
        )
        self.files = files
        self.human_feedback = human_feedback

        # workflow definition
        executor_workflow = StateGraph(AgentState)

        executor_workflow.add_node("agent", self.call_model_debugger)
        executor_workflow.add_node("tool", self.call_tool_debugger)
        executor_workflow.add_node("check_log", self.check_log)
        executor_workflow.add_node("human_help", agent_looped_human_help)
        executor_workflow.add_node("human_end_process_confirmation", ask_human)

        executor_workflow.set_entry_point("agent")

        # executor_workflow.add_edge("agent", "checker")
        executor_workflow.add_edge("tool", "agent")
        executor_workflow.add_edge("human_help", "agent")
        executor_workflow.add_conditional_edges("agent", self.after_agent_condition)
        executor_workflow.add_conditional_edges("check_log", self.after_check_log_condition)
        executor_workflow.add_conditional_edges("human_end_process_confirmation", after_ask_human_condition)

        self.executor = executor_workflow.compile()

    # node functions
    def call_model_debugger(self, state):
        state = call_model(state, llms)
        last_message = state["messages"][-1]
        if last_message.type == "ai" and len(last_message.json5_tool_calls) > 1:
            state["messages"].append(
                HumanMessage(content=multiple_jsons_msg))
            print_formatted("\nToo many jsons provided, asked to provide one.", color="yellow")
        return state

    def call_tool_debugger(self, state):
        last_ai_message = state["messages"][-1]
        state = call_tool(state, self.tool_executor)
        for tool_call in last_ai_message.json5_tool_calls:
            if tool_call["tool"] == "create_file_with_code":
                self.files.add(tool_call["tool_input"]["filename"])
        self.exchange_file_contents(state)
        return state

    def check_log(self, state):
        # Add logs
        logs = check_application_logs()
        log_message = HumanMessage(content="Logs:\n" + logs)

        state["messages"].append(log_message)
        return state

    # Conditional edge functions
    def after_agent_condition(self, state):
        last_message = state["messages"][-1]

        # safety mechanism for looped wrong tool call
        last_human_messages = [m for m in state["messages"] if m.type == "human"][-4:]
        tool_not_executed_msgs = [
            m for m in last_human_messages if isinstance(m.content, str) and m.content.startswith(TOOL_NOT_EXECUTED_WORD)
        ]
        if len(tool_not_executed_msgs) == 4:
            print("Seems like AI been looped. Please suggest it how to introduce change correctly:")
            return "human_help"

        elif last_message.content in (bad_json_format_msg, multiple_jsons_msg, no_json_msg):
            return "agent"
        elif last_message.json5_tool_calls[0]["tool"] == "final_response":
            return "check_log" if log_file_path else "human_end_process_confirmation"
        else:
            return "tool"

    def after_check_log_condition(self, state):
        last_message = state["messages"][-1]

        if last_message.content.endswith("Logs are correct"):
            return "human_end_process_confirmation"
        else:
            return "agent"

    # just functions
    def exchange_file_contents(self, state):
        # Remove old one
        state["messages"] = [msg for msg in state["messages"] if not hasattr(msg, "contains_file_contents")]
        # Add new file contents
        file_contents = check_file_contents(self.files, self.work_dir)
        file_contents_msg = HumanMessage(content=f"File contents:\n{file_contents}", contains_file_contents=True)
        state["messages"].insert(2, file_contents_msg)  # insert after the system and plan msgs
        return state

    def do_task(self, task, plan, text_files):
        print("\n\n\nExecutor starting its work")
        file_contents = check_file_contents(text_files, self.work_dir)
        inputs = {"messages": [
            self.system_message,
            HumanMessage(content=f"Task: {task}\n\n######\n\nPlan which developer implemented already:\n\n{plan}"),
            HumanMessage(content=f"File contents: {file_contents}", contains_file_contents=True),
            HumanMessage(content=f"Human feedback: {self.human_feedback}")
        ]}
        self.executor.invoke(inputs, {"recursion_limit": 150})


def prepare_tools(work_dir):
    list_dir = prepare_list_dir_tool(work_dir)
    see_file = prepare_see_file_tool(work_dir)
    replace_code = prepare_replace_code_tool(work_dir)
    insert_code = prepare_insert_code_tool(work_dir)
    create_file = prepare_create_file_tool(work_dir)
    tools = [list_dir, see_file, replace_code, insert_code, create_file, ask_human_tool, final_response]
    #if frontend_port:
    #    watch_web_page_tool = prepare_watch_web_page_tool(frontend_port)
    #    tools.append(watch_web_page_tool)

    return tools
