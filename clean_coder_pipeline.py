from agents.researcher_agent import research_task
from agents.planner_agent import planning
from agents.executor_agent import Executor


task = """
Let's work on memorial profile.
here is an example json with fulfilled education profile:
{'id': '018f53bc-32b7-799a-a813-0801daf5e0cf', 'isPrivate': False, 'firstName': 'Eukator', 'secondName': '', 'lastName': 'Jeden', 'familyName': '', 'birthDate': {'day': '', 'month': '', 'year': ''}, 'birthPlace': '', 'deathDate': {'day': '', 'month': '', 'year': ''}, 'deathPlace': '', 'photoUrl': [], 'sections': [{'id': '018f53bc-a533-77da-86ea-657c868b7d66', 'key': 'education', 'items': [{'id': '018f53bc-a533-77da-86ea-657d6cb7bd31', 'startYear': '1023', 'endYear': '1024', 'place': 'Kotków dolny', 'description': 'Uczył się długo i namiętnie, tylko po co?', 'photoUrl': ''}, {'id': '018f53bd-2bae-7629-a017-1a8135770f63', 'description': 'A i tak dzik', 'place': 'kotków inny', 'startYear': '2345', 'endYear': '4321'}]}], 'owner': '663a0eec22b346aad0dde283', 'slot_number': '85-83-93'}
Make education page show apropriate value. add different education pages for different items. do not show any education page if json not contains education section.
"""


files, file_contents, images = research_task(task)

plan = planning(task, file_contents, images)

executor = Executor(files)
executor.do_task(task, plan, file_contents)
