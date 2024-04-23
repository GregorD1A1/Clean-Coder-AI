from langchain_openai.chat_models import ChatOpenAI
from langchain.output_parsers import XMLOutputParser
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
    voter_messages: Sequence[BaseMessage]


system_message = SystemMessage(
    content="You are programmer and scrum master expert. You guiding your code monkey friend about what changes need to be done "
            "in code in order to execute given task. You describing in github format what code "
            "need to be inserted, deleted, replaced or which file created. Provide only the changes."
            "When writing your changes plan, you planning only code changes, neither library installation or tests or anything else."
            "At every your message, you providing proposition of all changes, not just some."
            "The user can't modify your code. So do not suggest incomplete code which requires users to modify."
)

voter_system_message = SystemMessage(
    content="You have a few proposed plans how to implement given task. Analyze, which of them solves task the best, "
            "fullfils criteria of providing complete code. Respond in xml with parameters <reasoning> and <choice>."
)


# node functions
def call_planers(state):
    nr_plans = 3
    plan_propositions = "Here are plan propositions:\n\n"
    for i in range(nr_plans):
        print(f"Generating plan proposition {i}/{nr_plans}...")
        messages = state["messages"]
        response = llm.invoke(messages)
        print_wrapped(response.content)
        plan_propositions += f"Proposition nr 1: " + response.content + "\n\n"

    state["voter_messages"].append(HumanMessage(content=plan_propositions))
    chain = llm | XMLOutputParser()
    response = chain.invoke(messages)
    print_wrapped(response.content)
    # add chosen plan to messages


    return state


def call_model_corrector(state):
    state, response = call_model(state, llm)
    return state


def ask_human_with_plan_printing(state):
    last_message = state["messages"][-1]
    print_wrapped(last_message.content, 100)
    return ask_human(state)


# workflow definition
researcher_workflow = StateGraph(AgentState)

researcher_workflow.add_node("planers", call_planers)
researcher_workflow.add_node("corrector", call_model_corrector)
researcher_workflow.add_node("human", ask_human_with_plan_printing)
researcher_workflow.set_entry_point("planers")

researcher_workflow.add_edge("planers", "human")
researcher_workflow.add_edge("corrector", "human")
researcher_workflow.add_conditional_edges("human", after_ask_human_condition)

researcher = researcher_workflow.compile()


def planning(task, file_contents, images):
    print("Planner starting its work")
    message_content = [f"Task: {task},\n\nFiles:\n{file_contents}"] + images
    message_from_researcher = HumanMessage(content=message_content)

    inputs = {
        "messages": [system_message, message_from_researcher],
        "voter_messages": [voter_system_message, message_from_researcher]
    }
    planner_response = researcher.invoke(inputs, {"recursion_limit": 50})["messages"][-2]

    return planner_response.content
