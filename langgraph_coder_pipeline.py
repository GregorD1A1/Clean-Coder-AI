from langgraph_coder.langgraph_researcher import researcher
from langchain_core.messages import HumanMessage
import json
from tools.tools_crew import see_file


inputs = {"messages": [HumanMessage(content="task: Create an endpoint that saves new post without asking user")]}
response = researcher.invoke(inputs)["messages"][-1]
files = json.loads(response.additional_kwargs["function_call"]["arguments"])["files_for_executor"]

file_contents = str()
for file_name in files:
    file_content = see_file(file_name)
    file_contents += "File: " + file_name + ":\n\n" + file_content + "\n\n###\n\n"

print(file_contents)