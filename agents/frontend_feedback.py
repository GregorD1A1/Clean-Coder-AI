import os
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from dotenv import load_dotenv, find_dotenv
from langchain.tools import tool
from langchain_community.chat_models import ChatOllama
from langchain_anthropic import ChatAnthropic
from utilities.llms import llm_open_router
from utilities.print_formatters import print_formatted
from utilities.start_project_functions import read_frontend_feedback_story
from utilities.util_functions import (
    check_file_contents, check_application_logs, render_tools, find_tools_json
)


llms = []
if os.getenv("ANTHROPIC_API_KEY"):
    llms.append(ChatAnthropic(
        model='claude-3-5-sonnet-20241022', temperature=0, max_tokens=2000, timeout=120
    ).with_config({"run_name": "Executor"}))
if os.getenv("OPENROUTER_API_KEY"):
    llms.append(llm_open_router("anthropic/claude-3.5-sonnet").with_config({"run_name": "Executor"}))
if os.getenv("OPENAI_API_KEY"):
    llms.append(ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=120).with_config({"run_name": "Executor"}))
if os.getenv("OLLAMA_MODEL"):
    llms.append(ChatOllama(model=os.getenv("OLLAMA_MODEL")).with_config({"run_name": "Executor"}))

llm = llms[0].with_fallbacks(llms[1:])

story = read_frontend_feedback_story()
story = story.format(frontend_port=5173)

# read prompt from file
parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
with open(f"{parent_dir}/prompts/frontend_feedback.prompt", "r") as f:
    prompt_template = f.read()

plan = """I want to be redirected to /register every time I go to /
"""
prompt = prompt_template.format(story=story, plan=plan)

response =llm.invoke(prompt)
print(response.content)