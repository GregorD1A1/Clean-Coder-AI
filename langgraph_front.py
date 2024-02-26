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

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Check out all the files that could be needed to execute the task. Do not do the task, just make "
            "filesystem research to prepare ground for task executor."
            " You have access to the following tools: {tool_names}.\n{system_message}",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


# This a helper class we have that is useful for running tools
# It takes in an agent action and calls that tool and returns the result
tool_executor = ToolExecutor(tools)


def call_model(state):
    print("state:", state)
    messages = state["messages"][-5:]
    """ + [
        SystemMessage(
            content="Check out all the files that could be needed to execute the task. Do not do the task, just make "
                    "filesystem research to prepare ground for task executor."
        )
    ]"""
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


# Define logic that will be used to determine which conditional edge to go down
def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    # If there is no function call, then we finish
    if "function_call" not in last_message.additional_kwargs:
        return "end"
    # Otherwise we continue
    else:
        return "continue"


# Define a new graph
workflow = StateGraph(AgentState)
workflow.state = {"messages": [SystemMessage(content="task: Change time to log out user after unactivity to 120m")]}

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("action", call_tool)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.set_entry_point("agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
    # Finally we pass in a mapping.
    # The keys are strings, and the values are other nodes.
    # END is a special node marking that the graph should finish.
    # What will happen is we will call `should_continue`, and then the output of that
    # will be matched against the keys in this mapping.
    # Based on which one it matches, that node will then be called.
    {
        # If `tools`, then we call the tool node.
        "continue": "action",
        # Otherwise we finish.
        "end": END,
    },
)

workflow.add_edge("action", "agent")

# Finally, we compile it!
# This compiles it into a LangChain Runnable,
# meaning you can use it as you would any other runnable
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