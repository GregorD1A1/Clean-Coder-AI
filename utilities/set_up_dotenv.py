"""
File with functions allowing to set up api keys in .env file.

As that functions are set up in the beginning of work process, avoid improrting anything from other files. (Especially from files where env variables are needed).
"""
from termcolor import colored


def set_up_env_coder_pipeline():
    envs = {}
    print(colored("🖐  Hey! Let's set up our project.", color="cyan"))
    print(colored("1/2. Provide one or more API keys for LLM providers or the local Ollama model. Don't worry, you can always modify them in the .env file.", color="cyan"))
    envs["ANTHROPIC_API_KEY"] = input("Please provide your Anthropic API key (Optional):\n")
    envs["OPENAI_API_KEY"] = input("Please provide your OpenAI API key (Optional):\n")
    envs["OPEN_ROUTER_API_KEY"] = input("Please provide your Open Router API key (Optional):\n")
    envs["OLLAMA_MODEL"] = input("Please provide your Ollama model name (Optional):\n")
    print(colored("2/2. Now provide the folder containing your project.", color="cyan"))
    envs["WORK_DIR"] = input("Please provide your work directory:\n")
    # save them to file
    with open(".env", "w") as f:
        for key, value in envs.items():
            f.write(f"{key}={value}\n")
    print(colored("We have done .env file set up! You can modify your variables in any moment in .env.\n", color="green"))


def set_up_env_manager():
    envs = {}
    print(colored("🖐  Hey! Let's set up our project.", color="cyan"))
    print(colored("1/3. Provide one or more API keys for LLM providers or the local Ollama model. Don't worry, you can always modify them in the .env file.", color="cyan"))
    envs["ANTHROPIC_API_KEY"] = input("Please provide your Anthropic API key (Optional):\n")
    envs["OPENAI_API_KEY"] = input("Please provide your OpenAI API key (Optional):\n")
    envs["OPEN_ROUTER_API_KEY"] = input("Please provide your Open Router API key(Optional):\n")
    envs["OLLAMA_MODEL"] = input("Please provide your Ollama model name(Optional):\n")
    print(colored("2/3. Now provide the folder containing your project.", color="cyan"))
    envs["WORK_DIR"] = input("Please provide your work directory:\n")
    print(colored("3/3. Now let's set up your Todoist connection.", color="cyan"))
    envs["TODOIST_API_KEY"] = input("Please provide your Todoist API key:\n")
    envs["TODOIST_PROJECT_ID"] = input("Please provide your Todoist project ID:\n")

    with open(".env", "w") as f:
        for key, value in envs.items():
            f.write(f"{key}={value}\n")
    print(colored("We have done .env file set up! You can modify your variables in any moment in .env.\n", color="green"))


def add_todoist_envs():
    envs = {}
    print(colored("1/1. Now let's set up your Todoist connection.", color="cyan"))
    envs["TODOIST_API_KEY"] = input("Please provide your Todoist API key:\n")
    envs["TODOIST_PROJECT_ID"] = input("Please provide your Todoist project ID:\n")

    with open(".env", "a+") as f:
        for key, value in envs.items():
            f.write(f"{key}={value}\n")
    print(colored("We have done .env file set up! You can modify your variables in any moment in .env.\n", color="green"))
