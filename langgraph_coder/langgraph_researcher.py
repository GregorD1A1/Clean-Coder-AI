from tools.tools_crew import list_dir, see_file
from langchain_openai.chat_models import ChatOpenAI
from typing import TypedDict, Annotated, List, Sequence
from langchain_core.messages import BaseMessage
import operator
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph import END, StateGraph
from dotenv import load_dotenv, find_dotenv
from langchain.tools.render import format_tool_to_openai_function
from langgraph.prebuilt import ToolInvocation
import json
from langchain_core.messages import FunctionMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.utils.function_calling import convert_pydantic_to_openai_function
from langchain_core.messages import HumanMessage, SystemMessage


load_dotenv(find_dotenv())


class FinalResponse(BaseModel):
    """Final response containing lList of files executor will need to change. Use that tool only when you 100% sure
    you found all the files Executor will need to modify. If not, do additional research."""
    reasoning: str = Field(description="Reasoning what files will needed")
    files_for_executor: List[str] = Field(description="List of files")


tools = [list_dir, see_file]
llm = ChatOpenAI(model="gpt-4-turbo-preview", streaming=True)

functions = [format_tool_to_openai_function(t) for t in tools]
functions.append(convert_pydantic_to_openai_function(FinalResponse))
llm = llm.bind_functions(functions)


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


tool_executor = ToolExecutor(tools)


def call_model(state):
    messages = state["messages"] + [
        SystemMessage(
            content="You are helping your friend Executor to make provided task. Don't do it by yourself."
                    "Make filesystem research and provide files that executor will need to change in order to do his "
                    "task. Never recommend file you haven't seen yet."
        )
    ]
    response = llm.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


def call_tool(state):
    last_message = state["messages"][-1]

    action = ToolInvocation(
        tool=last_message.additional_kwargs["function_call"]["name"],
        tool_input=json.loads(
            last_message.additional_kwargs["function_call"]["arguments"]
        ),
    )
    response = tool_executor.invoke(action)
    # We use the response to create a FunctionMessage
    function_message = FunctionMessage(content=str(response), name=action.tool)
    # We return a list, because this will get added to the existing list
    return {"messages": [function_message]}


def ask_human(state):
    last_message = state["messages"][-1]

    human_response = input(last_message.content)
    if not human_response:
        return {"messages": [HumanMessage(content="Approved by human")]}
    else:
        return {"messages": [HumanMessage(content=human_response)]}


# Logic for conditional edges
def after_agent_condition(state):
    last_message = state["messages"][-1]

    if "function_call" not in last_message.additional_kwargs:
        return "human"
    elif last_message.additional_kwargs["function_call"]["name"] == "FinalResponse":
        return "end"
    else:
        return "continue"


# workflow definition
researcher_workflow = StateGraph(AgentState)

researcher_workflow.add_node("agent", call_model)
researcher_workflow.add_node("tool", call_tool)
researcher_workflow.add_node("human", ask_human)

researcher_workflow.set_entry_point("agent")

researcher_workflow.add_conditional_edges(
    "agent",
    after_agent_condition,
    {
        "continue": "tool",
        "human": "human",
        "end": END,
    },
)

researcher_workflow.add_edge("tool", "agent")
researcher_workflow.add_edge("human", "agent")

researcher = researcher_workflow.compile()

if __name__ == "__main__":
    inputs = {"messages": [HumanMessage(content="task: Create an endpoint that saves new post without asking user")]}
    #response = researcher.invoke(inputs)
    #print(response)

    for output in researcher.stream(inputs):
        # stream() yields dictionaries with output keyed by node name
        for key, value in output.items():
            print(f"Output from node '{key}':")
            print("---")
            print(value)
        print("\n---\n")