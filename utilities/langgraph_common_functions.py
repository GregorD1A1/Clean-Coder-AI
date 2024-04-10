from langchain_core.messages import HumanMessage


def ask_human(state=None):
    human_response = input("Write 'ok' if you agree with a researched files or provide commentary.")
    if human_response == "ok":
        return {"messages": [HumanMessage(content="Approved by human")]}
    else:
        return {"messages": [HumanMessage(content=human_response)]}