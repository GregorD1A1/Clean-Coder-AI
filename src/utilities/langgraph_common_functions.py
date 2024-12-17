from langchain_core.messages import HumanMessage
from src.utilities.print_formatters import print_formatted, print_error, print_formatted_content, print_formatted_content
from src.utilities.util_functions import invoke_tool, invoke_tool_native, TOOL_NOT_EXECUTED_WORD
from src.utilities.user_input import user_input
from langgraph.graph import END
from src.utilities.graphics import loading_animation
import threading
import sys


multiple_tools_msg = TOOL_NOT_EXECUTED_WORD + """You made multiple tool calls at once. If you want to execute 
multiple actions, choose only one for now; rest you can execute later."""
no_tools_msg = TOOL_NOT_EXECUTED_WORD + """Please provide a tool call to execute an action."""
finish_too_early_msg = TOOL_NOT_EXECUTED_WORD + """You want to call final response with other tool calls. Don't you finishing too early?"""


# nodes
def _start_loading_animation():
    loading_animation.is_running = True
    thread = threading.Thread(target=loading_animation)
    thread.daemon = True
    thread.start()
    return thread


def _stop_loading_animation(thread):
    loading_animation.is_running = False
    thread.join()


def _get_llm_response(llms, messages, printing):
    for llm in llms:
        try:
            return llm.invoke(messages)
        except Exception as e:
            if printing:
                print_formatted(
                    f"\nException happened: {e} with llm: {llm.bound.__class__.__name__}. "
                    "Switching to next LLM if available...",
                    color="yellow"
                )
    if printing:
        print_formatted("Can not receive response from any llm", color="red")
    sys.exit()


def call_model(state, llms, printing=True):
    messages = state["messages"]
    loading_thread = None

    if printing:
        loading_thread = _start_loading_animation()

    response = _get_llm_response(llms, messages, printing)
    if printing and loading_thread:
        _stop_loading_animation(loading_thread)

    if printing:
        print_formatted_content(response)
    state["messages"].append(response)

    return state

def call_tool(state, tools):
    last_message = state["messages"][-1]
    tool_response_messages = [invoke_tool_native(tool_call, tools) for tool_call in last_message.tool_calls]
    state["messages"].extend(tool_response_messages)
    return state


def ask_human(state):
    human_message = user_input("Type (o)k if you accept or provide commentary.")
    if human_message in ['o', 'ok']:
        state["messages"].append(HumanMessage(content="Approved by human"))
    else:
        state["messages"].append(HumanMessage(content=human_message))
    return state


def agent_looped_human_help(state):
    human_message = user_input(
        "It seems the agent repeatedly tries to introduce wrong changes. Help him to find his mistakes."
    )
    state["messages"].append(HumanMessage(content=human_message))
    return state


# conditions
def after_ask_human_condition(state):
    last_message = state["messages"][-1]

    if last_message.content == "Approved by human":
        return END
    else:
        return "agent"
