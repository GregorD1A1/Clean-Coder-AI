from langchain_openai.chat_models import ChatOpenAI
from langchain.output_parsers import XMLOutputParser
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import END, StateGraph
from dotenv import load_dotenv, find_dotenv
from utilities.util_functions import print_wrapped, check_file_contents, convert_images, get_joke
from utilities.langgraph_common_functions import call_model, ask_human, after_ask_human_condition
import os
from langchain_community.chat_models import ChatOllama
from langchain_anthropic import ChatAnthropic


load_dotenv(find_dotenv())

llm = ChatOpenAI(model="gpt-4o", temperature=0.3).with_config({"run_name": "Planer"})
llm_voter = llm.with_config({"run_name": "Voter"})


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]
    voter_messages: Sequence[BaseMessage]

current_dir = os.path.dirname(os.path.realpath(__file__))
with open(f"{current_dir}/prompts/planer_system.prompt", "r") as f:
    planer_system_prompt_template = f.read()
with open(f"{current_dir}/prompts/voter_system.prompt", "r") as f:
    voter_system_prompt_template = f.read()

planer_system_message = SystemMessage(content=planer_system_prompt_template)
voter_system_message = SystemMessage(content=voter_system_prompt_template)


# node functions
def call_planers(state):
    messages = state["messages"]
    nr_plans = 3
    print(f"\nGenerating plan propositions. While I'm thinking...\n")
    print_wrapped(get_joke(), color="red")
    plan_propositions_messages = llm.batch([messages for _ in range(nr_plans)])
    for i, proposition in enumerate(plan_propositions_messages):
        state["voter_messages"].append(AIMessage(content="_"))
        state["voter_messages"].append(HumanMessage(content=f"Proposition nr {i+1}:\n\n" + proposition.content))

    print("Choosing the best plan...")
    chain = llm_voter | XMLOutputParser()
    response = chain.invoke(state["voter_messages"])

    choice = int(response["response"][2]["choice"])
    plan = plan_propositions_messages[choice - 1]
    state["messages"].append(plan)
    print_wrapped(f"Chosen plan:\n\n{plan.content}")

    return state


def call_model_corrector(state):
    messages = state["messages"]
    response = llm.invoke(messages)
    print_wrapped(response.content)
    state["messages"].append(response)

    return state


# workflow definition
researcher_workflow = StateGraph(AgentState)


researcher_workflow.add_node("planers", call_planers)
researcher_workflow.add_node("agent", call_model_corrector)
researcher_workflow.add_node("human", ask_human)
researcher_workflow.set_entry_point("planers")

researcher_workflow.add_edge("planers", "human")
researcher_workflow.add_edge("agent", "human")
researcher_workflow.add_conditional_edges("human", after_ask_human_condition)

researcher = researcher_workflow.compile()


def planning(task, text_files, image_paths, work_dir):
    print("\n\n\nPlanner starting its work")
    file_contents = check_file_contents(text_files, work_dir)
    images = convert_images(image_paths)
    message_content_without_imgs = f"Task: {task},\n\nFiles:\n{file_contents}"
    message_without_imgs = HumanMessage(content=message_content_without_imgs)
    message_images = HumanMessage(content=images)

    inputs = {
        "messages": [planer_system_message, message_without_imgs, message_images],
        "voter_messages": [voter_system_message, message_without_imgs],
    }
    planner_response = researcher.invoke(inputs, {"recursion_limit": 50})["messages"][-2]

    return planner_response.content


if __name__ == "__main__":
    task = "Test task"
    work_dir = os.getenv("WORK_DIR")
    planning(task, work_dir=work_dir)