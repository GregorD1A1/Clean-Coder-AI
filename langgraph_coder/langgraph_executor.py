import os
import re
import json
from langgraph_coder.tools.tools import see_file, modify_code, insert_code, create_file_with_code, check_application_logs
from langchain_openai.chat_models import ChatOpenAI
from typing import TypedDict, Annotated, List, Sequence
from langchain_core.messages import BaseMessage
import operator
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph import END, StateGraph
from dotenv import load_dotenv, find_dotenv
from langgraph.prebuilt import ToolInvocation
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.tools.render import render_text_description
from langchain.tools import tool
from langchain_community.chat_models import ChatOllama
from langchain_anthropic import ChatAnthropic


load_dotenv(find_dotenv())


@tool
def final_response():
    """Call that tool when all planned changes are implemented."""
    pass


tools = [see_file, modify_code, insert_code, create_file_with_code, final_response]
rendered_tools = render_text_description(tools)

llm = ChatOpenAI(model="gpt-4-turbo-preview", streaming=True)
#llm = ChatAnthropic(model='claude-3-opus-20240229')
#llm = ChatOllama(model="mixtral"), temperature=0)


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


tool_executor = ToolExecutor(tools)
system_message = SystemMessage(
        content="You are senior programmer. You need to improve existing code using provided tools. Introduce changes "
                "from plan one by one, means you can write only one json with change in that step."
                "You prefer to initiate your modifications from the higher line numbers within the code. "
                "This method prevents subsequent amendments from incorrectly overwriting the previously adjusted file."
                "\n\n"
                "You have access to following tools:\n"
                f"{rendered_tools}"
                "\n\n"
                "To use tool, strictly follow json blob:"
                "```json"
                "{"
                " 'tool': '$TOOL_NAME',"
                " 'tool_input': '$TOOL_PARAMETERS',"
                "}"
                "```"
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


def check_file_contents(files):
    file_contents = str()
    for file_name in files:
        file_content = see_file(file_name)
        file_contents += "File: " + file_name + ":\n\n" + file_content + "\n\n###\n\n"

    return file_contents


# Logic for conditional edges
def after_agent_condition(state):
    last_message = state["messages"][-1]

    if not last_message.tool_call:
        return "go_human"
    if last_message.tool_call["tool"] == "final_response":
        return "end"
    else:
        return "continue"


def after_check_log_condition(state):
    last_message = state["messages"][-1]

    if last_message.content.endswith("Logs are healthy."):
        return "end"
    else:
        return "return"


def after_ask_human_condition(state):
    last_message = state["messages"][-1]

    if last_message.content == "Approved by human":
        return "end"
    else:
        return "return"



class Executor():
    def __init__(self, files):
        self.files = files

        # workflow definition
        executor_workflow = StateGraph(AgentState)

        executor_workflow.add_node("agent", self.call_model)
        executor_workflow.add_node("tool", self.call_tool)
        executor_workflow.add_node("check_log", self.check_files_and_log)
        executor_workflow.add_node("human", self.ask_human)

        executor_workflow.set_entry_point("agent")

        executor_workflow.add_conditional_edges(
            "agent",
            after_agent_condition,
            {
                "continue": "tool",
                "end": "check_log",
                "go_human": "human",
            },
        )
        executor_workflow.add_conditional_edges(
            "check_log",
            after_check_log_condition,
            {
                "return": "agent",
                "end": "human",
            }
        )
        executor_workflow.add_conditional_edges(
            "human",
            after_ask_human_condition,
            {
                "return": "agent",
                "end": END,
            }
        )
        executor_workflow.add_edge("tool", "agent")

        self.executor = executor_workflow.compile()

    # node functions
    def call_model(self, state):
        messages = state["messages"]  # + [system_message]
        response = llm.invoke(messages)
        tool_call_json = find_tool_json(response.content)
        response.tool_call = tool_call_json
        # We return a list, because this will get added to the existing list
        return {"messages": [response]}

    def call_tool(self, state):
        last_message = state["messages"][-1]
        tool_call = last_message.tool_call
        response = tool_executor.invoke(ToolInvocation(**tool_call))
        response_message = HumanMessage(content=str(response), name=tool_call["tool"])

        return {"messages": [response_message]}

    def ask_human(self, state):
        last_message = state["messages"][-1]

        human_response = input("Write 'ok' to confirm end of execution or provide commentary.")
        if human_response == "ok":
            return {"messages": [HumanMessage(content="Approved by human")]}
        else:
            return {"messages": [HumanMessage(content=human_response)]}

    def check_files_and_log(self, state):
        file_contents = check_file_contents(self.files)
        logs = check_application_logs()
        # logs = input("Write 'ok' to continue or paste logs of error (Use that feature only for backend).")
        if logs == "ok":
            message = file_contents + "\n\n###\n\n" + "Logs are healthy."
        else:
            message = file_contents + "\n\n###\n\n" + logs

        return {"messages": [HumanMessage(content=message)]}


    def do_task(self, task, plan, file_contents):
        print("Executor starting its work")
        inputs = {"messages": [system_message,HumanMessage(content=f"Task: {task}\n\nPlan: {plan}\n\nFile contents: {file_contents}")]}
        executor_response = self.executor.invoke(inputs, {"recursion_limit": 100})["messages"][-1]

if __name__ == "__main__":
    executor.get_graph().draw_png()
