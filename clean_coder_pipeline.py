from agents.researcher_agent import research_task
from agents.planner_agent import planning
from agents.executor_agent import Executor


task = """
In the cover page of mem profile, let's make button "poznaj historię" working - it should scroll to the next page down. see final page, here some ref.

Example json:
{'id': '018f626f-0279-7b60-ae9e-b295434c9a73', 'isPrivate': False, 'firstName': 'Jonh', 'secondName': 'Doe', 'lastName': 'Koń', 'familyName': '', 'birthDate': {'day': '12', 'month': '12', 'year': '1234'}, 'birthPlace': 'kotkowp', 'deathDate': {'day': '11', 'month': '2', 'year': '4443'}, 'deathPlace': '', 'mainPhotoUrl': 'static\\018f626f-0279-7b60-ae9e-b295434c9a73\\personal_details_x_15e3879d494261d24f70c0a7cab7d533977d7d7202a9c587aa7af8aecc391f06.png', 'sections': [{'id': '018f626f-da0c-7d3d-a6ff-50a234788a40', 'key': 'work', 'items': [{'id': '018f626f-da0c-7d3d-a6ff-50a3c51e0c99', 'startYear': '2211', 'endYear': '2222', 'place': 'dzikstwo', 'description': 'było ciekawie. kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk.mmmmmmmmmmmmmmmmmmmmmasndsnnsdnsssssssssssssssssssssssssss', 'photoUrl': 'static\\018f626f-0279-7b60-ae9e-b295434c9a73\\work_018f626f-da0c-7d3d-a6ff-50a3c51e0c99_3bb1ccf699797d0e35ef429f7184630aa875d3069c202b559144dd4dad689606.jpg'}]}, {'id': '018f6270-b366-7b80-8827-629a471af69d', 'key': 'important_events', 'items': [{'id': '018f6270-b366-7b80-8827-629ba9c46cc2', 'day': '12', 'month': '2', 'year': '2211', 'title': 'xdd', 'description': 'sssssssssssssssssssssssssssssssss', 'photoUrl': 'static\\018f626f-0279-7b60-ae9e-b295434c9a73\\important_event_018f6270-b366-7b80-8827-629ba9c46cc2_082203a5b650d9550cf1a3882a9853954847553fa0ff4fb4712e069ecc1949a1.png'}, {'id': '018f6271-0ccc-749f-9f5f-70ebc14dc98e', 'day': '1', 'month': '6', 'year': '2222', 'title': 'qqqqqqqqqqqqqqqqqqqqqqqqqqq', 'description': '', 'photoUrl': 'static\\018f626f-0279-7b60-ae9e-b295434c9a73\\important_event_018f6271-0ccc-749f-9f5f-70ebc14dc98e_10d90d95c7844b1db74ad8571ca1b50ba28607d3250ab88b53c6fedab4b16b00.jpg'}]}], 'owner': '663a0eec22b346aad0dde283', 'slot_number': '56-67-57'}
"""

task = """
make tooltip in the dashboard page to be showing slighly above "udestępnij button and on the right side.
"""


files, file_contents, images = research_task(task)

plan = planning(task, file_contents, images)

executor = Executor(files)
executor.do_task(task, plan, file_contents)
