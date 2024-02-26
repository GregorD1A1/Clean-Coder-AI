from tools.tools_crew import list_dir, see_file
from langchain.agents import create_openai_functions_agent
from langchain_openai.chat_models import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from typing import TypedDict, Annotated, List, Union, Sequence
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import BaseMessage
import operator
from langchain_core.agents import AgentFinish
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph import END, StateGraph
from dotenv import load_dotenv, find_dotenv
from langchain.tools.render import format_tool_to_openai_function
from langgraph.prebuilt import ToolInvocation
import json
from langchain_core.messages import FunctionMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.utils.function_calling import convert_pydantic_to_openai_function
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


load_dotenv(find_dotenv())

tools = [list_dir, see_file]
llm = ChatOpenAI(model="gpt-4-turbo-preview", streaming=True)

functions = [format_tool_to_openai_function(t) for t in tools]
llm = llm.bind_functions(functions)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


# This a helper class we have that is useful for running tools
# It takes in an agent action and calls that tool and returns the result
tool_executor = ToolExecutor(tools)


def call_model(state):
    print("state:", state)
    messages = state["messages"] + [
        SystemMessage(
            content="You are helping your friend Executor to make provided task. Don't do it by yourself."
                    "Make filesystem research and provide file that executor will need to change in order to do his "
                    "task."
        )
    ]
    response = llm.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


# Define the function to execute tools
def execute_tools(data):
    # Get the most recent agent_outcome - this is the key added in the `agent` above
    agent_action = data["agent_outcome"]
    output = tool_executor.invoke(agent_action)
    return {"intermediate_steps": [(agent_action, str(output))]}

def call_tool(state):
    messages = state["messages"]
    # Based on the continue condition
    # we know the last message involves a function call
    last_message = messages[-1]
    # We construct an ToolInvocation from the function_call
    action = ToolInvocation(
        tool=last_message.additional_kwargs["function_call"]["name"],
        tool_input=json.loads(
            last_message.additional_kwargs["function_call"]["arguments"]
        ),
    )
    # We call the tool_executor and get back a response
    response = tool_executor.invoke(action)
    # We use the response to create a FunctionMessage
    function_message = FunctionMessage(content=str(response), name=action.tool)
    # We return a list, because this will get added to the existing list
    return {"messages": [function_message]}

def ask_human(state):
    messages = state["messages"]
    last_message = messages[-1]

    human_response = input(last_message.content)
    if not human_response:
        return {"messages": [HumanMessage(content="Approved by human")]}
    else:
        return {"messages": [HumanMessage(content=human_response)]}

# Define logic that will be used to determine which conditional edge to go down
def after_agent_condition(state):
    messages = state["messages"]
    last_message = messages[-1]

    if "function_call" not in last_message.additional_kwargs:
        return "human"
    else:
        return "continue"


def after_human_condition(state):
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.content == "Approved by human":
        return "end"
    else:
        return "agent"


workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tool", call_tool)
workflow.add_node("human", ask_human)

workflow.set_entry_point("agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    "agent",
    after_agent_condition,
    {
        "continue": "tool",
        "human": "human",
        "end": END,
    },
)

workflow.add_conditional_edges(
    "human",
    after_human_condition,
    {
        "continue": "agent",
        "end": END,
    }
)

workflow.add_edge("tool", "agent")
workflow.add_edge("human", "agent")

app = workflow.compile()


inputs = {"messages": [HumanMessage(content="task: Change time to log out user after unactivity to 120m")]}
#response = app.invoke(inputs)
#print(response)

for output in app.stream(inputs):
    # stream() yields dictionaries with output keyed by node name
    for key, value in output.items():
        print(f"Output from node '{key}':")
        print("---")
        print(value)
    print("\n---\n")