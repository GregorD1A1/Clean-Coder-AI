from langchain_openai.chat_models import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ChatMessageHistory
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())

def human_approval(message: str) -> str:
    return input(f"Plan:\n{message}\n\nWrite 'ok' to approve plan or provide commentary with suggestions to improve:\n")


class Planer():
    def __init__(self, task, file_contents):
        system_message = SystemMessage(
            content="You are programmer and scrum master expert. Your task is to propose what changes need to be done "
                    "in code or which files created in order to execute given task. You carefully describing what code"
                    "to insert with line nr providing. Not paste all the file code, but only lines to change/insert."
                    "You not providing any library installation commands or other bash commands, some other "
                    "agent will do it, only proposing code changes."
                    "At every your message, you providing proposition of the entire plan, not just one part of it."
                    "When you feel that more files need to be changed than provided on your input, you talking about it."
        )
        human_message = HumanMessage(content=
                    f"Task is: {task}"
                    "Files:"
                    f"{file_contents}")
        prompt = ChatPromptTemplate.from_messages([system_message, human_message, MessagesPlaceholder(variable_name="messages")])
        llm = ChatOpenAI(model="gpt-4", temperature=0.3)
        #llm = ChatAnthropic(model='claude-3-opus-20240229', temperature=0.3)
        self.chain = prompt | llm | StrOutputParser()

    def plan(self):
        print("Planer starting its work")
        human_commentary = "something"
        memory = ChatMessageHistory()
        while human_commentary != "ok":
            plan_proposition = self.chain.invoke({"messages": memory.messages})
            memory.add_ai_message(plan_proposition)
            human_commentary = human_approval(plan_proposition)
            memory.add_user_message(human_commentary)

        return plan_proposition

if __name__ == '__main__':
    task = "print 4 instead"
    file_contents = "print(2)"
    planer = Planer(task, file_contents)
    plan = planer.plan()
    print(plan)