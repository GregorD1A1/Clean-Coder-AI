from langchain_openai.chat_models import ChatOpenAI as ChatOpenRouter
from os import getenv
from dotenv import load_dotenv

load_dotenv()

def llm_open_router(model):
    return ChatOpenRouter(
    openai_api_key=getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    model_name=model,
    default_headers={
        "HTTP-Referer": "https://github.com/GregorD1A1/Clean-Coder-AI",
        "X-Title": "Clean Coder",
    },
    timeout=60,
)
