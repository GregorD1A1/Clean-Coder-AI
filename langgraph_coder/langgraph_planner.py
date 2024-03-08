from langchain_openai.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ChatMessageHistory
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())

def human_approval(message: str) -> str:
    return input(f"Plan:\n{message}\n\nHit enter to approve plan or provide commentary with suggestons to improve:\n")


class Planer():
    def __init__(self, task, file_contents):
        system_message = SystemMessage(
            content="You are programmer and scrum master expert. Your task is to propose what changes need to be done "
                    "in code in order to execute given task. You carefully describing what code to insert with line nr "
                    "providing. You not providing any library installation comands or other bash commands, some other "
                    "agent will do it, only proposing code changes."
                    f"Task is: {task}"
                    "Files:"
                    f"{file_contents}"
        )
        prompt = ChatPromptTemplate.from_messages([system_message, MessagesPlaceholder(variable_name="messages")])
        llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
        self.chain = prompt | llm | StrOutputParser()

    def plan(self):
        print("Planer strating its work")
        human_commentary = "something"
        memory = ChatMessageHistory()
        while human_commentary:
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