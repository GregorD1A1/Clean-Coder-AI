from langchain_core.messages import HumanMessage
from utilities.util_functions import find_tool_json, print_wrapped
from langgraph.prebuilt import ToolInvocation
from langgraph.graph import END


# nodes
def call_model(state, llm):
    messages = state["messages"]
    response = llm.invoke(messages)
    tool_call_json = find_tool_json(response.content)
    response.tool_call = tool_call_json
    print_wrapped(response.content)
    state["messages"].append(response)
    return state


def call_tool(state, tool_executor):
    last_message = state["messages"][-1]
    if not hasattr(last_message, "tool_call"):
        state["messages"].append(HumanMessage(content="No tool called"))
        return state
    tool_call = last_message.tool_call
    response = tool_executor.invoke(ToolInvocation(**tool_call))
    response_message = HumanMessage(content=str(response))
    state["messages"].append(response_message)

    return state


def ask_human(state):
    human_response = input("Write 'ok' if you agree with a researched files or provide commentary. ")
    if human_response == "ok":
        state["messages"].append(HumanMessage(content="Approved by human"))
    else:
        state["messages"].append(HumanMessage(content=human_response))
    return state

# conditions
def after_ask_human_condition(state):
    last_message = state["messages"][-1]

    if last_message.content == "Approved by human":
        return END
    else:
        return "agent"