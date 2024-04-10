from langchain_openai.chat_models import ChatOpenAI
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
import operator
from langgraph.graph import END, StateGraph
from dotenv import load_dotenv, find_dotenv
from langchain_community.chat_models import ChatOllama
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from utilities.util_functions import print_wrapped
from utilities.langgraph_common_functions import ask_human


load_dotenv(find_dotenv())

llm = ChatOpenAI(model="gpt-4-vision-preview", temperature=0.2)
#llm = ChatAnthropic(model='claude-3-opus-20240229')
#llm = ChatOllama(model="mixtral") #, temperature=0)


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


system_message = SystemMessage(
    content="You are programmer and scrum master expert. You guiding your code monkey friend about what changes need to be done "
            "in code in order to execute given task. You describing in github format what code "
            "need to be inserted, deleted, replaced or which file created."
            "When writing your changes plan, you planning only code changes, neither library installation or tests or anything else."
            "At every your message, you providing proposition of all changes, not just some."
)


# working on that function for future
def choose_files_for_executor(plan, files):
    prompt = PromptTemplate.from_template(
        "Based on provided plan, return list of files that need to be changed. Choose files from original list:\n"
        "{files}\n\nPlan: \n{plan}")
    chain = prompt | llm
    chain.invoke({"plan": plan, "files": files})


# node functions
def call_model(state):
    messages = state["messages"]
    response = llm.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


def ask_human_with_plan_printing(state):
    last_message = state["messages"][-1]
    print_wrapped(last_message.content, 100)
    return ask_human()


# Logic for conditional edges
def after_ask_human_condition(state):
    last_message = state["messages"][-1]

    if last_message.content == "Approved by human":
        return END
    else:
        return "agent"


# workflow definition
researcher_workflow = StateGraph(AgentState)

researcher_workflow.add_node("agent", call_model)
researcher_workflow.add_node("human", ask_human_with_plan_printing)
researcher_workflow.set_entry_point("agent")

researcher_workflow.add_edge("agent", "human")
researcher_workflow.add_conditional_edges("human", after_ask_human_condition)

researcher = researcher_workflow.compile()


def planning(message_from_researcher):
    print("Planner starting its work")
    inputs = {"messages": [system_message, message_from_researcher]}
    # try max_iterations instead of recursion_limit
    planner_response = researcher.invoke(inputs, {"recursion_limit": 50})["messages"][-2]

    return planner_response
