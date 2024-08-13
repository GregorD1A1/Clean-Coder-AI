from langchain_openai.chat_models import ChatOpenAI
from langchain.output_parsers import XMLOutputParser
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import END, StateGraph
from dotenv import load_dotenv, find_dotenv
from langchain_community.chat_models import ChatOllama
from langchain_anthropic import ChatAnthropic
from utilities.util_functions import print_wrapped
from utilities.langgraph_common_functions import call_model, ask_human, after_ask_human_condition
from langchain_groq import ChatGroq


load_dotenv(find_dotenv())

llm = ChatOpenAI(model="gpt-4o", temperature=0.3).with_config({"run_name": "Planer"})
#llm = ChatOpenAI(model="gpt-4-vision-preview", temperature=0.3).with_config({"run_name": "Planer"})
#llm_voter = ChatAnthropic(model='claude-3-opus-20240229')
#llm = ChatOllama(model="mixtral") #, temperature=0)
llm_voter = llm.with_config({"run_name": "Voter"})
llm_secretary = llm


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]
    voter_messages: Sequence[BaseMessage]
    secretary_messages: Sequence[BaseMessage]


system_message = SystemMessage(
    content="""
You are senior programmer. You guiding your code monkey friend about what changes need to be done in code in order 
to execute given task. Think step by step and provide detailed plan about what code modifications needed to be done 
to execute task. When possible, plan consistent code with other files. Your recommendations should include in details:
- Details about functions modifications - provide only functions you want to replace, without rest of the file,
- Details about movement lines and functionalities from file to file,
- Details about new file creation,
Plan should not include library installation or tests or anything else unrelated to code modifications.
At every your message, you providing proposition of all changes, not just some. Never imagine files you have 
not provided in context. Simplicity is a priority - write minimum needed amount of code.

Do not rewrite full code, instead only write changes and point places where they need to be inserted. 
Show with pluses (+) and minuses (-), where you want to add/remove code.
Example:
- self.id_number = str(ObjectId())
+ self.user_id = str(ObjectId())
+ self.email = email

"""
)


voter_system_message = SystemMessage(
    content="""
    Several implementation plans for a task implementation have been proposed. Carefully analyze these plans and 
    determine which one accomplishes the task most effectively.
    Take in account the following criteria:
    1. The primary criterion is the effectiveness of the plan in executing the task. It is most important.
    2. A secondary criterion is simplicity. If two plans are equally good, chose one described more concise and required 
    less modifications.
    3. The third criterion is consistency with existing code in other files. Prefer plan with code more similar to existing codebase.
    
    Respond in xml:
    ```xml
    <response>
        <evaluating>
            Neatly summarize characteristics of plan propositions. Impartially evaluate pros and cons of every of them.
        </evaluating>
        <weighting>
           Think step by step about why one proposition is better than another. Make final decision which of them is the
           best according to provided criteria.
        </weighting>
        <choice>
           Provide here nr of plan you chosen. Only the number and nothing more.
        </choice>
    </response>
    ```
    """
)

secretary_system_message = SystemMessage(
    content="""
You are secretary of lead developer. You have provided plan proposed by lead developer. Analyze the plan and find if all 
proposed changes are related to provided list of project files only, or lead dev need to check other files also.

Return in:
```xml
<response>
<reasoning>
Think step by step if some additional files are needed for that plan or not.
</reasoning>
<message_to_file_researcher>
Write 'No any additional files needed.' if all the proposed plan changes are in given files; write custom message with 
request to check out files in filesystem if plan assumes changes in another files than provided or lead dev wants to 
ensure about something in another files.
</message_to_file_researcher>
<response>
```
"""
)


# node functions
def call_planers(state):
    messages = state["messages"]
    nr_plans = 3
    print(f"\nGenerating plan propositions...")
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
    state, response = call_model(state, llm)
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


def planning(task, file_contents, images):
    print("\n\n\nPlanner starting its work")
    message_content_without_imgs = f"Task: {task},\n\nFiles:\n{file_contents}"
    message_without_imgs = HumanMessage(content=message_content_without_imgs)
    message_images = HumanMessage(content=images)

    inputs = {
        "messages": [system_message, message_without_imgs, message_images],
        "voter_messages": [voter_system_message, message_without_imgs],
        "secretary_messages": [secretary_system_message]
    }
    planner_response = researcher.invoke(inputs, {"recursion_limit": 50})["messages"][-2]

    return planner_response.content
