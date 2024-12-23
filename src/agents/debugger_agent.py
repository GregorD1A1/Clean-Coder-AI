import os
from src.tools.tools_coder_pipeline import (
    ask_human_tool, prepare_list_dir_tool, prepare_see_file_tool,
    prepare_create_file_tool, prepare_replace_code_tool, prepare_insert_code_tool
)
from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph
from dotenv import load_dotenv, find_dotenv
from langchain.tools import tool
from src.utilities.print_formatters import print_formatted
from src.utilities.util_functions import check_file_contents, check_application_logs, exchange_file_contents, bad_tool_call_looped
from src.utilities.llms import init_llms
from src.utilities.langgraph_common_functions import (
    call_model, call_tool, ask_human, after_ask_human_condition, multiple_tools_msg, no_tools_msg,
    agent_looped_human_help,
)
from src.agents.frontend_feedback import execute_screenshot_codes

load_dotenv(find_dotenv())
log_file_path = os.getenv("LOG_FILE")
frontend_port = os.getenv("FRONTEND_PORT")


@tool
def final_response_debugger(test_instruction):
    """Call that tool when all changes are implemented to tell the job is done.
tool input:
:param test_instruction: write detailed instruction for human what actions he need to do in order to check if
implemented changes work correctly."""  # noqa: D205, D207, D209, D213
    pass

class AgentState(TypedDict):
    messages: Sequence[BaseMessage]


parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

with open(f"{parent_dir}/prompts/debugger_system.prompt", "r") as f:
    system_prompt_template = f.read()


class Debugger():
    def __init__(self, files, work_dir, human_feedback, vfeedback_screenshots_msg=None, playwright_codes=None, screenshot_descriptions=None):
        self.work_dir = work_dir
        self.tools = prepare_tools(work_dir)
        self.llms = init_llms(self.tools, "Debugger")
        self.system_message = SystemMessage(
            content=system_prompt_template
        )
        self.files = files
        self.human_feedback = human_feedback
        self.visual_feedback = vfeedback_screenshots_msg
        self.playwright_codes = playwright_codes
        self.screenshot_descriptions = screenshot_descriptions

        # workflow definition
        debugger_workflow = StateGraph(AgentState)

        debugger_workflow.add_node("agent", self.call_model_debugger)
        debugger_workflow.add_node("check_log", self.check_log)
        debugger_workflow.add_node("frontend_screenshots", self.frontend_screenshots)
        debugger_workflow.add_node("human_help", agent_looped_human_help)
        debugger_workflow.add_node("human_end_process_confirmation", ask_human)

        debugger_workflow.set_entry_point("agent")

        debugger_workflow.add_edge("human_help", "agent")
        debugger_workflow.add_edge("frontend_screenshots", "human_end_process_confirmation")
        debugger_workflow.add_conditional_edges("agent", self.after_agent_condition)
        debugger_workflow.add_conditional_edges("check_log", self.after_check_log_condition)
        debugger_workflow.add_conditional_edges("human_end_process_confirmation", after_ask_human_condition)

        self.debugger = debugger_workflow.compile()

    # node functions
    def call_model_debugger(self, state):
        state = call_model(state, self.llms)
        state = self.call_tool_debugger(state)
        return state

    def call_tool_debugger(self, state):
        state = call_tool(state, self.tools)
        messages = [msg for msg in state["messages"] if msg.type == "ai"]
        last_ai_message = messages[-1]
        if len(last_ai_message.tool_calls) > 1:
            for tool_call in last_ai_message.tool_calls:
                state["messages"].append(ToolMessage(content="too much tool calls", tool_call_id=tool_call["id"]))
            state["messages"].append(HumanMessage(content=multiple_tools_msg))
        state = exchange_file_contents(state, self.files, self.work_dir)
        return state

    def check_log(self, state):
        # Add logs
        logs = check_application_logs()
        log_message = HumanMessage(content="Logs:\n" + logs)
        state["messages"].append(log_message)

        return state

    def frontend_screenshots(self, state):
        print_formatted("Making screenshots, please wait a while...", color="light_blue")
        # Remove old one
        state["messages"] = [msg for msg in state["messages"] if not hasattr(msg, "contains_screenshots")]
        # Add new file contents
        screenshot_msg = execute_screenshot_codes(self.playwright_codes, self.screenshot_descriptions)
        state["messages"].append(screenshot_msg)
        return state

    # Conditional edge functions
    def after_agent_condition(self, state):
        messages = [msg for msg in state["messages"] if msg.type in ["ai", "human"]]
        last_message = messages[-1]

        if bad_tool_call_looped(state):
            return "human_help"
        elif last_message.tool_calls and last_message.tool_calls[0]["name"] == "final_response_debugger":
            if log_file_path:
                return "check_log"
            elif self.screenshot_descriptions:
                return "frontend_screenshots"
            else:
                return "human_end_process_confirmation"
        else:
            return "agent"

    def after_check_log_condition(self, state):
        last_message = state["messages"][-1]

        if last_message.content.endswith("Logs are correct"):
            if self.screenshot_descriptions:
                return "frontend_screenshots"
            else:
                return "human_end_process_confirmation"
        else:
            return "agent"

    def do_task(self, task, plan):
        print_formatted("Debugger starting its work", color="green")
        print_formatted("🛠️ Need to improve your code? I can help!", color="light_blue")
        file_contents = check_file_contents(self.files, self.work_dir)
        inputs = {"messages": [
            self.system_message,
            HumanMessage(content=f"Task: {task}\n\n######\n\nPlan which developer implemented already:\n\n{plan}"),
            HumanMessage(content=f"File contents: {file_contents}", contains_file_contents=True),
            HumanMessage(content=f"Human feedback: {self.human_feedback}")
        ]}
        if self.visual_feedback:
            inputs["messages"].append(self.visual_feedback)
        self.debugger.invoke(inputs, {"recursion_limit": 150})


def prepare_tools(work_dir):
    list_dir = prepare_list_dir_tool(work_dir)
    see_file = prepare_see_file_tool(work_dir)
    replace_code = prepare_replace_code_tool(work_dir)
    insert_code = prepare_insert_code_tool(work_dir)
    create_file = prepare_create_file_tool(work_dir)
    tools = [list_dir, see_file, replace_code, insert_code, create_file, ask_human_tool, final_response_debugger]

    return tools
