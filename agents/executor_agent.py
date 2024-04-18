import os
from tools.tools import see_file, replace_code, insert_code, create_file_with_code
from langchain_openai.chat_models import ChatOpenAI
from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph import StateGraph
from dotenv import load_dotenv, find_dotenv
from langchain.tools.render import render_text_description
from langchain.tools import tool
from langchain_community.chat_models import ChatOllama
from langchain_anthropic import ChatAnthropic
from utilities.util_functions import check_file_contents, print_wrapped, check_application_logs
from utilities.langgraph_common_functions import call_model, call_tool, ask_human, after_ask_human_condition


load_dotenv(find_dotenv())
log_file_path = os.getenv("LOG_FILE")


@tool
def final_response():
    """Call that tool when all planned changes are implemented."""
    pass


tools = [see_file, insert_code, replace_code, create_file_with_code, final_response]
rendered_tools = render_text_description(tools)

llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
#llm = ChatAnthropic(model='claude-3-opus-20240229')
#llm = ChatOllama(model="mixtral"), temperature=0)


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]


tool_executor = ToolExecutor(tools)
system_message = SystemMessage(
        content="You are senior programmer. You need to improve existing code using provided tools. Introduce changes "
                "from plan one by one, means you can write only one json with change in that step."
                "You are working with smaller parts of code - modify single functions or lines rather then entire file."
                "\n\n"
                "You have access to following tools:\n"
                f"{rendered_tools}"
                "\n\n"
                "To use tool, strictly follow json blob:"
                "```json"
                "{"
                " 'reasoning': '$STEP_BY_STEP_REASONING_ABOUT_WHICH_TOOL_TO_USE_AND_WITH_WHICH_PARAMETERS',"
                " 'tool': '$TOOL_NAME',"
                " 'tool_input': '$TOOL_PARAMETERS',"
                "}"
                "```"
    )


class Executor():
    def __init__(self, files):
        self.files = files

        # workflow definition
        executor_workflow = StateGraph(AgentState)

        executor_workflow.add_node("agent", self.call_model_executor)
        executor_workflow.add_node("tool", self.call_tool_executor)
        executor_workflow.add_node("check_log", self.check_log)
        executor_workflow.add_node("human", ask_human)

        executor_workflow.set_entry_point("agent")

        executor_workflow.add_conditional_edges("agent", self.after_agent_condition)
        executor_workflow.add_conditional_edges("check_log", self.after_check_log_condition,)
        executor_workflow.add_conditional_edges("human", after_ask_human_condition)
        executor_workflow.add_edge("tool", "agent")

        self.executor = executor_workflow.compile()

    # node functions
    def call_model_executor(self, state):
        return call_model(state, llm)

    def call_tool_executor(self, state):
        last_message = state["messages"][-1]
        state = call_tool(state, tool_executor)
        if last_message.tool_call["tool"] == "create_file_with_code":
            self.files.append(last_message.tool_call["tool_input"]["filename"])
        if last_message.tool_call["tool"] in ["insert_code", "modify_code", "create_file_with_code"]:
            state = self.exchange_file_contents(state)
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

        if not last_message.tool_call:
            return "human"
        if last_message.tool_call["tool"] == "final_response":
            if log_file_path:
                return "check_log"
            else:
                return "human"
        else:
            return "tool"

    def after_check_log_condition(self, state):
        last_message = state["messages"][-1]

        if last_message.content.endswith("Logs are correct"):
            return "human"
        else:
            return "agent"

    # just functions
    def exchange_file_contents(self, state):
        # Remove old one
        state["messages"] = [msg for msg in state["messages"] if not hasattr(msg, "contains_file_contents")]
        # Add new file contents
        file_contents = check_file_contents(self.files)
        file_contents_msg = HumanMessage(content=f"File contents:\n{file_contents}", contains_file_contents=True)
        state["messages"].append(file_contents_msg)
        return state

    def do_task(self, task, plan, file_contents):
        print("Executor starting its work")
        inputs = {"messages": [
            system_message,
            HumanMessage(content=f"Task: {task}\n\n###\n\nPlan: {plan}"),
            HumanMessage(content=f"File contents: {file_contents}", contains_file_contents=True)
        ]}
        self.executor.invoke(inputs, {"recursion_limit": 150})["messages"][-1]
