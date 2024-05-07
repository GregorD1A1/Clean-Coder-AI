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
from utilities.util_functions import check_file_contents, print_wrapped, check_application_logs, find_tool_json
from utilities.langgraph_common_functions import call_model, call_tool, ask_human, after_ask_human_condition


load_dotenv(find_dotenv())
log_file_path = os.getenv("LOG_FILE")


@tool
def final_response(dummy_argument):
    """Call that tool when all changes are implemented to tell the job is done. If you have no idea which tool to call,
    call that."""
    pass


tools = [see_file, insert_code, replace_code, create_file_with_code, final_response]
rendered_tools = render_text_description(tools)

checker_llm = ChatOpenAI(model="gpt-4-turbo", temperature=0).with_config({"run_name": "Checker"})
llm = ChatOpenAI(model="gpt-4-turbo", temperature=0).with_config({"run_name": "Executor"})
#llm = ChatAnthropic(model='claude-3-opus-20240229').with_config({"run_name": "Executor"})
#llm = ChatOllama(model="mixtral"), temperature=0).with_config({"run_name": "Executor"})


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]
    checker_response: str


tool_executor = ToolExecutor(tools)
system_message = SystemMessage(
        content=f"""
You are a senior programmer tasked with refining an existing codebase. Your goal is to incrementally 
introduce improvements using a set of provided tools. Each change should be implemented step by step, 
meaning you make one modification at a time. Focus on enhancing individual functions or lines of code 
rather than rewriting entire files at once.
\n\n
Tools to your disposal:\n
{rendered_tools}
\n\n
First, write your thinking process. Think step by step about what do you need to do to accomplish the task. 
Next, call one tool using template:
```json
{{
    "tool": "$TOOL_NAME",
    "tool_input": "$TOOL_PARAMS",
}}
```
"""
    )

checker_system_message = SystemMessage(
    content=f"""
You are senior programmer. Your task is to check out work of a junior programmer. Junior will propose modifications into
existing file in order to execute task. Check out if his modifications not include mistakes.

Possible scenarios:
1. Line numbers for code insertion or replacement are mistaken. A common error involves forgetting to include the 
existing closing bracket when replacing an entire function or code block, resulting in writing the ending line number 
right before the closing bracket. Check out line numbers produced by junior carefully.
2. Junior forgot to add indent (spaces) on the beginning of his code. If there are some spaces, everything ok.
3. Provided line numbers are correct and indents are in place. Code is valid.

Return your answer as json:
```json
{{
    "reasoning": "Reasoning if junior made some mistakes or not. Discuss here function/piece of code we work on.",
    "response": "Write 'Everything ok.' only if no mistakes mentioned. Otherwise, explain the problem for your teammate",
}}
```
"""
)


class Executor():
    def __init__(self, files):
        self.files = files

        # workflow definition
        executor_workflow = StateGraph(AgentState)

        executor_workflow.add_node("agent", self.call_model_executor)
        #executor_workflow.add_node("checker", self.call_model_checker)
        executor_workflow.add_node("tool", self.call_tool_executor)
        executor_workflow.add_node("check_log", self.check_log)
        executor_workflow.add_node("human", ask_human)

        executor_workflow.set_entry_point("agent")

        #executor_workflow.add_edge("agent", "checker")
        executor_workflow.add_edge("tool", "agent")
        executor_workflow.add_conditional_edges("agent", self.after_agent_condition)
        executor_workflow.add_conditional_edges("check_log", self.after_check_log_condition)
        executor_workflow.add_conditional_edges("human", after_ask_human_condition)

        self.executor = executor_workflow.compile()

    # node functions
    def call_model_executor(self, state):
        state, _ = call_model(state, llm)
        return state

    def call_model_checker(self, state):
        last_message = state["messages"][-1]
        exector_message = HumanMessage(content=last_message.content)
        checker_messages = [
            checker_system_message, exector_message
        ]

        # adding file content
        if getattr(last_message, "tool_call", None) and last_message.tool_call["tool"] in ["insert_code", "replace_code"]:
            file = last_message.tool_call["tool_input"]["filename"]
            file_content = see_file(file)
            file_content_message = HumanMessage(content=file_content)
            checker_messages.insert(1, file_content_message)

        response = checker_llm.invoke(checker_messages)
        print_wrapped(f"Checker response:  {response.content}", color="red")
        message = find_tool_json(response.content)["response"]
        state["checker_response"] = message
        if message != "Everything ok.":
            state["messages"].append(HumanMessage(content=f"Execution interrupted. Checker message: {message}"))
        return state


    def call_tool_executor(self, state):
        last_message = state["messages"][-1]
        state = call_tool(state, tool_executor)
        if last_message.tool_call["tool"] == "create_file_with_code":
            self.files.add(last_message.tool_call["tool_input"]["filename"])
        if last_message.tool_call["tool"] in ["insert_code", "replace_code", "create_file_with_code"]:
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
            return "agent"
        elif last_message.tool_call["tool"] != "final_response":
            return "tool"
        else:
            print("inside of final response condition")
            return "check_log" if log_file_path else "human"

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
