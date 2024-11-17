from langchain_core.load import dumps, load

from langchain_core.messages import HumanMessage, AIMessage

messages = [
    HumanMessage(content="Hello, how are you?"),
    AIMessage(content="I'm fine, thank you!")
]
json_representation = dumps(messages, pretty=True)

messages = load(json_representation)
print(messages)