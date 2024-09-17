from langchain_core.messages import HumanMessage
from utilities.util_functions import find_tool_json, print_formatted
from utilities.user_input import user_input
from langgraph.prebuilt import ToolInvocation
from langgraph.graph import END
from langchain_core.messages.ai import AIMessage
from tools.tools_coder_pipeline import TOOL_NOT_EXECUTED_WORD

bad_json_format_msg = TOOL_NOT_EXECUTED_WORD + """Bad json format. Json should be enclosed with '```json', '```' tags.
Code inside of json should be provided in the way that not makes json invalid.
No '```' tags should be inside of json."""
multiple_jsons_msg = TOOL_NOT_EXECUTED_WORD + """You have written multiple jsons at once. If you want to execute 
multiple actions, choose only one for now; rest you can execute later."""
no_json_msg = TOOL_NOT_EXECUTED_WORD + """Please provide a json tool call to execute an action."""


# nodes
def call_model(state, llm, stop_sequence_to_add=None):
    messages = state["messages"]
    response = llm.invoke(messages)
    # Replicate returns string instead of AI Message, we need to handle it
    if 'Replicate' in str(llm):
        response = AIMessage(content=str(response))
    # Add stop sequence if needed (sometimes needed for Claude)
    response.content = response.content + stop_sequence_to_add if stop_sequence_to_add else response.content
    response.tool_call = find_tool_json(response.content)
    print_formatted(response.content)
    state["messages"].append(response)

    # safety mechanism for a bad json
    tool_call = response.tool_call
    if tool_call == "Multiple jsons found.":
        state["messages"].append(
            HumanMessage(content=multiple_jsons_msg))
        print("\nToo many jsons provided, asked to provide one.")
    elif tool_call == "No json found in response.":
        state["messages"].append(HumanMessage(content=no_json_msg))
        print("\nNo json provided, asked to provide one.")
    if tool_call is None or "tool" not in tool_call:
        state["messages"].append(HumanMessage(content=bad_json_format_msg))
        print("\nBad json format provided, asked to provide again.")

    return state


def call_tool(state, tool_executor):
    last_message = state["messages"][-1]
    if not hasattr(last_message, "tool_call"):
        state["messages"].append(HumanMessage(content="No tool called"))
        return state
    tool_call = last_message.tool_call
    response = tool_executor.invoke(ToolInvocation(**tool_call))
    '''
    try:
        response = tool_executor.invoke(ToolInvocation(**tool_call))
    except Exception as e:
        print("Error in tool call formatting")
        response = "Some error in tool call format. Are you sure that you provided all needed tool parameters according tool schema?"
    '''
    response_message = HumanMessage(content=str(response))
    state["messages"].append(response_message)

    return state


def ask_human(state):
    human_message = user_input("Type (o)k if you accept or provide commentary.")
    if human_message in ['o', 'ok']:
        state["messages"].append(HumanMessage(content="Approved by human"))
    else:
        state["messages"].append(HumanMessage(content=human_message))
    return state


# conditions
def after_ask_human_condition(state):
    last_message = state["messages"][-1]

    if last_message.content == "Approved by human":
        return END
    else:
        return "agent"
