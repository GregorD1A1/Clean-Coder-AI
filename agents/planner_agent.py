from langchain_openai.chat_models import ChatOpenAI
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from dotenv import load_dotenv, find_dotenv
from langchain_community.chat_models import ChatOllama
from langchain_anthropic import ChatAnthropic
from utilities.util_functions import print_wrapped
from utilities.langgraph_common_functions import call_model, ask_human, after_ask_human_condition


load_dotenv(find_dotenv())

llm = ChatOpenAI(model="gpt-4-vision-preview", temperature=0.2)
#llm = ChatAnthropic(model='claude-3-opus-20240229')
#llm = ChatOllama(model="mixtral") #, temperature=0)


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]


system_message = SystemMessage(
    content="You are programmer and scrum master expert. You guiding your code monkey friend about what changes need to be done "
            "in code in order to execute given task. You describing in github format what code "
            "need to be inserted, deleted, replaced or which file created."
            "When writing your changes plan, you planning only code changes, neither library installation or tests or anything else."
            "At every your message, you providing proposition of all changes, not just some."
            "The user can't modify your code. So do not suggest incomplete code which requires users to modify."
)


# node functions
def call_model_planner(state):
    return call_model(state, llm)


def ask_human_with_plan_printing(state):
    last_message = state["messages"][-1]
    print_wrapped(last_message.content, 100)
    return ask_human(state)


# workflow definition
researcher_workflow = StateGraph(AgentState)

researcher_workflow.add_node("agent", call_model_planner)
researcher_workflow.add_node("human", ask_human_with_plan_printing)
researcher_workflow.set_entry_point("agent")

researcher_workflow.add_edge("agent", "human")
researcher_workflow.add_conditional_edges("human", after_ask_human_condition)

researcher = researcher_workflow.compile()


def planning(message_from_researcher):
    print("Planner starting its work")
    inputs = {"messages": [system_message, message_from_researcher]}
    planner_response = researcher.invoke(inputs, {"recursion_limit": 50})["messages"][-2]

    return planner_response.content
