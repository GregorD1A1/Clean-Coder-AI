import re
import json
from langgraph_coder.tools.tools import list_dir, see_file, image_to_code
from langgraph_coder.utilities.util_functions import print_wrapped
from langchain_openai.chat_models import ChatOpenAI
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
import operator
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph import END, StateGraph
from dotenv import load_dotenv, find_dotenv
from langgraph.prebuilt import ToolInvocation
from langchain.tools.render import render_text_description
from langchain_community.chat_models import ChatOllama
from langchain_anthropic import ChatAnthropic


load_dotenv(find_dotenv())


tools = [list_dir, see_file, image_to_code]
rendered_tools = render_text_description(tools)

#llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.2)
llm = ChatAnthropic(model='claude-3-opus-20240229')
#llm = ChatOllama(model="mixtral") #, temperature=0)


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


tool_executor = ToolExecutor(tools)
system_message = SystemMessage(
    content="You have access to following tools:\n"
            f"{rendered_tools}"
            "\n\n"
            "To use tool, make your output in valid json format and strictly follow blob:"
            "```json"
            "{"
            " 'reasoning': '$STEP_BY_STEP_REASONING_ABOUT_WHICH_TOOL_AND_WITH_WHICH_PARAMETERS_TO_USE',"
            " 'tool': '$TOOL_NAME',"
            " 'tool_input': '$TOOL_PARAMETERS',"
            "}"
            "```"
            "You are programmer and scrum master expert. You guiding your code monkey friend about what changes need to be done "
            "in code in order to execute given task. You describing in github format what code "
            "need to be inserted, deleted, replaced or which file created."
            "You need to print all the code need to be changed, do not miss any line."
            "When writing your plan, you planning only code changes, neither library installation or tests or anything else."
            "At every your message, you providing proposition of the entire plan, not just one part of it."
            "Even use tool or write your plan."
)


def find_tool_json(response):
    match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)

    if match:
        json_str = match.group(1).strip()
        print("Tool call: ", json_str)
        json_obj = json.loads(json_str)
        return json_obj
    else:
        return None


# node functions
def call_model(state):
    messages = state["messages"]
    response = llm.invoke(messages)
    tool_call_json = find_tool_json(response.content)
    if tool_call_json:
        response.tool_call = tool_call_json
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


def call_tool(state):
    last_message = state["messages"][-1]
    tool_call = last_message.tool_call
    response = tool_executor.invoke(ToolInvocation(**tool_call))
    response_message = HumanMessage(content=str(response))

    return {"messages": [response_message]}


def ask_human(state):
    last_message = state["messages"][-1]
    print_wrapped(last_message.content)
    human_response = input("Write 'ok' if you agree with a researched files or provide commentary.")
    if human_response == "ok":
        return {"messages": [HumanMessage(content="Approved by human")]}
    else:
        return {"messages": [HumanMessage(content=human_response)]}


# Logic for conditional edges
def after_agent_condition(state):
    last_message = state["messages"][-1]
    if not hasattr(last_message, "tool_call"):
        return "human"
    else:
        return "tool"


def after_ask_human_condition(state):
    last_message = state["messages"][-1]

    if last_message.content == "Approved by human":
        return END
    else:
        return "agent"


# workflow definition
researcher_workflow = StateGraph(AgentState)

researcher_workflow.add_node("agent", call_model)
researcher_workflow.add_node("tool", call_tool)
researcher_workflow.add_node("human", ask_human)
researcher_workflow.set_entry_point("agent")

researcher_workflow.add_conditional_edges("agent", after_agent_condition)
researcher_workflow.add_conditional_edges("human", after_ask_human_condition)
researcher_workflow.add_edge("tool", "agent")

researcher = researcher_workflow.compile()


def planning(task, file_contents):
    print("Planner starting its work")
    inputs = {"messages": [system_message, HumanMessage(content=f"task: {task},\n\n files: {file_contents}")]}
    # try max_iterations instead of recursion_limit
    planner_response = researcher.invoke(inputs, {"recursion_limit": 50})["messages"][-2]
    #tool_json = find_tool_json(planner_response.content)["tool_input"]
    #plan = tool_json["plan"]
    #files = tool_json["files_for_executor"]

    return planner_response
