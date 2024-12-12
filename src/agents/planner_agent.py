from langchain_openai.chat_models import ChatOpenAI
from langchain.output_parsers import XMLOutputParser
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import END, StateGraph
from dotenv import load_dotenv, find_dotenv

from src.utilities.print_formatters import print_formatted, print_formatted_content
from src.utilities.util_functions import check_file_contents, convert_images, get_joke
from src.utilities.langgraph_common_functions import after_ask_human_condition
from src.utilities.user_input import user_input
import os
from langchain_community.chat_models import ChatOllama
from langchain_anthropic import ChatAnthropic
from src.utilities.llms import llm_open_router


load_dotenv(find_dotenv())

llms_planners = []
if os.getenv("OPENAI_API_KEY"):
    llms_planners.append(ChatOpenAI(model="gpt-4o", temperature=0.3, timeout=90).with_config({"run_name": "Planer"}))
if os.getenv("OPENROUTER_API_KEY"):
    llms_planners.append(llm_open_router("anthropic/claude-3.5-sonnet").with_config({"run_name": "Planer"}))
if os.getenv("ANTHROPIC_API_KEY"):
    llms_planners.append(ChatAnthropic(model='claude-3-5-sonnet-20241022', temperature=0.3, timeout=90).with_config({"run_name": "Planer"}))
if os.getenv("OLLAMA_MODEL"):
    llms_planners.append(ChatOllama(model=os.getenv("OLLAMA_MODEL")).with_config({"run_name": "Planer"}))

llm_planner = llms_planners[0].with_fallbacks(llms_planners[1:])
# copy planers, but exchange config name
llm_voter = llm_planner.with_config({"run_name": "Voter"})


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]
    voter_messages: Sequence[BaseMessage]


parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

with open(f"{parent_dir}/prompts/planer_system.prompt", "r") as f:
    planer_system_prompt_template = f.read()
with open(f"{parent_dir}/prompts/voter_system.prompt", "r") as f:
    voter_system_prompt_template = f.read()

planer_system_message = SystemMessage(content=planer_system_prompt_template)
voter_system_message = SystemMessage(content=voter_system_prompt_template)


# node functions
def call_planers(state):
    messages = state["messages"]
    nr_plans = 3
    print_formatted(get_joke(), color="green")
    plan_propositions_messages = llm_planner.batch([messages for _ in range(nr_plans)])
    for i, proposition in enumerate(plan_propositions_messages):
        state["voter_messages"].append(AIMessage(content="_"))
        state["voter_messages"].append(HumanMessage(content=f"Proposition nr {i+1}:\n\n" + proposition.content))

    print("Choosing the best plan...")
    chain = llm_voter | XMLOutputParser()
    response = chain.invoke(state["voter_messages"])

    choice = int(response["response"][2]["choice"])
    plan = plan_propositions_messages[choice - 1]

    state["messages"].append(plan)

    # Process and print the content
    print_formatted(f"Chosen plan:", color="light_blue")
    print_formatted_content(plan.content)
    print_formatted(f"\nPlease read the plan carefully. Never accept plan you don't understand.", color="light_blue")

    return state


def ask_human_planner(state):
    human_message = user_input("Type (o)k if you accept or provide commentary.")
    if human_message in ['o', 'ok']:
        state["messages"].append(HumanMessage(content="Approved by human"))
    else:
        state["messages"].append(HumanMessage(
            content=f"Plan been rejected by human. Improve it following his commentary: {human_message}"
        ))
    return state


def call_model_corrector(state):
    messages = state["messages"]
    response = llm_planner.invoke(messages)
    print_formatted_content(response.content)
    state["messages"].append(response)

    return state


# workflow definition
researcher_workflow = StateGraph(AgentState)

researcher_workflow.add_node("planers", call_planers)
researcher_workflow.add_node("agent", call_model_corrector)
researcher_workflow.add_node("human", ask_human_planner)
researcher_workflow.set_entry_point("planers")

researcher_workflow.add_edge("planers", "human")
researcher_workflow.add_edge("agent", "human")
researcher_workflow.add_conditional_edges("human", after_ask_human_condition)

researcher = researcher_workflow.compile()


def planning(task, text_files, image_paths, work_dir):
    print_formatted("📈 Planner here! Create plan of changes with me!", color="light_blue")
    file_contents = check_file_contents(text_files, work_dir, line_numbers=False)
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
