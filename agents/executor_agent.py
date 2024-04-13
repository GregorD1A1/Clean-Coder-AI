from tools.tools import see_file, modify_code, insert_code, create_file_with_code
from langchain_openai.chat_models import ChatOpenAI
from typing import TypedDict, Annotated, List, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph import END, StateGraph
from dotenv import load_dotenv, find_dotenv
from langgraph.prebuilt import ToolInvocation
from langchain.tools.render import render_text_description
from langchain.tools import tool
from langchain_community.chat_models import ChatOllama
from langchain_anthropic import ChatAnthropic
from utilities.util_functions import check_file_contents, print_wrapped, find_tool_json, check_application_logs
from utilities.langgraph_common_functions import ask_human


load_dotenv(find_dotenv())


@tool
def final_response():
    """Call that tool when all planned changes are implemented."""
    pass


tools = [see_file, modify_code, insert_code, create_file_with_code, final_response]
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


# Logic for conditional edges
def after_agent_condition(state):
    last_message = state["messages"][-1]

    if not last_message.tool_call:
        return "human"
    if last_message.tool_call["tool"] == "final_response":
        return "check_log"
    else:
        return "tool"


def after_check_log_condition(state):
    last_message = state["messages"][-1]

    if last_message.content.endswith("Logs are healthy."):
        return "human"
    else:
        return "agent"


def after_ask_human_condition(state):
    last_message = state["messages"][-1]

    if last_message.content == "Approved by human":
        return END
    else:
        return "agent"


class Executor():
    def __init__(self, files):
        self.files = files

        # workflow definition
        executor_workflow = StateGraph(AgentState)

        executor_workflow.add_node("agent", self.call_model)
        executor_workflow.add_node("tool", self.call_tool)
        executor_workflow.add_node("check_log", self.check_log)
        executor_workflow.add_node("human", self.ask_human_executor)

        executor_workflow.set_entry_point("agent")

        executor_workflow.add_conditional_edges(
            "agent",
            after_agent_condition,
        )
        executor_workflow.add_conditional_edges(
            "check_log",
            after_check_log_condition,
        )
        executor_workflow.add_conditional_edges(
            "human",
            after_ask_human_condition,
        )
        executor_workflow.add_edge("tool", "agent")

        self.executor = executor_workflow.compile()

    # node functions
    def call_model(self, state):
        messages = state["messages"]
        response = llm.invoke(messages)
        tool_call_json = find_tool_json(response.content)
        response.tool_call = tool_call_json
        state["messages"].append(response)
        return state

    def call_tool(self, state):
        last_message = state["messages"][-1]
        if not hasattr(last_message, "tool_call"):
            state["messages"].append(HumanMessage(content="no tool called"))
            return state
        tool_call = last_message.tool_call
        response = tool_executor.invoke(ToolInvocation(**tool_call))

        response_message = HumanMessage(content=str(response))
        state["messages"].append(response_message)
        if last_message.tool_call["tool"] in ["insert_code", "modify_code"]:
            state = self.exchange_file_contents(state)
        if last_message.tool_call["tool"] == "create_file_with_code":
            self.files.append(last_message.tool_call["tool_input"]["filename"])
        return state

    def check_log(self, state):
        # Add logs
        logs = check_application_logs()
        # logs = input("Write 'ok' to continue or paste logs of error (Use that line only for backend).")
        if logs == "ok":
            log_message = HumanMessage(content="Logs are healthy.")
        else:
            log_message = HumanMessage(content="Logs:\n" + logs)

        state["messages"].append(log_message)
        return state

    def ask_human_executor(self, state):
        human_response = ask_human(state)
        state["messages"].append(human_response)
        return state

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
        executor_response = self.executor.invoke(inputs, {"recursion_limit": 150})["messages"][-1]
