import os
from crewai import Agent, Task, Crew, Process
from langchain_community.chat_models import ChatOpenAI
from tools.tools_crew import list_dir, see_file, insert_code, modify_code, check_application_logs
from langchain.agents import load_tools
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())

human_tool = load_tools(["human"])[0]

# Define your agents with roles and goals
manager = Agent(
    role='Manager',
    goal='Provide plan of implementing backend features and delegate implementing it.',
    backstory="""
    Head of the project. When working on some task, first need to check all the files that could be useful. Next you 
    analyzing step-by-step how to implement given feature. You writing very detailed plan, including names of functions
    and lines in the file you want to be modified. After plan is ready, human needs to accept it. After human acceptance,
    you delegate to Engineer implementation of changes. Engineer can write and modify code and will execute the changes.
    """,
    verbose=True,
    tools=[list_dir, see_file, human_tool],
    allow_delegation=True,
    llm=ChatOpenAI(model_name="gpt-4-turbo-preview", temperature=0.5)
)

engineer = Agent(
  role='Engineer',
  goal='Implement backend features.',
  backstory="""
    You are imlementing backend features that Manager told you. 
    After making code changes, checkfile code again and check application logs to ensure changes
    are not caused any problems. If yes, repare it.
    
    If I plan assumes work on more than one file, work with files one by one. Introduce changes, check, repair,
    next file.
    
    After job done, confirm with human that functionality is ready.""",
  verbose=True,
  allow_delegation=False,
  tools=[human_tool, list_dir, see_file, insert_code, modify_code, check_application_logs],
  llm=ChatOpenAI(model_name="gpt-4-1106-preview", temperature=0.3)
)

# Create tasks for your agents

task1 = Task(
    description="""
    in tests/test_client_registration.py override_get_db function could not get called.
    Please check it out ind improve the file.
    
    If it will work for a first try, I'll give you 10000$ commission!
    """,
    agent=manager,
)

# Instantiate your crew with a sequential process
crew = Crew(
  agents=[manager, engineer],
  tasks=[task1],
  verbose=1, # You can set it to 1 or 2 to different logging levels
)

# Get your crew to work!
result = crew.kickoff()

print("######################")
print(result)
