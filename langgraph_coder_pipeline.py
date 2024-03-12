from langgraph_coder.langgraph_researcher import research_task
from langgraph_coder.langgraph_planner import Planer
from langgraph_coder.langgraph_executor import do_task


task = ("We want to divide post creation form for 4 different components, that will show one after another."
        "In that task let's add view nr 1, where user will be asked if created post needs to be public or private."
        "Rest of settings leave for the page 2, which is existing page. Do not create pages 3 and 4 yet."
        "Changes will sent to backend after submitting last page (currently page 2)."
        "Use session storage to remember changes between the steps."
        ""
        "Here you have description for the first page:"
        "'''"
        "1. There's a main heading or title at the top of the page that reads 'Tworzenie karty zmarłego,' which suggests that this interface is for creating some sort of profile or card for a deceased individual."
        "2. Just below the main title, there's a subheading 'Krok 1 z 4: Widoczność profilu,' indicating that this is step 1 of a 4-step process, specifically concerning the visibility of the profile."
        "3. The page content is divided into sections by horizontal lines, which serve to separate the title, subheading, and main content area for a clean and organized layout."
        "4. The main content area starts with a section header 'Widoczność profilu,' which reiterates the focus on profile visibility."
        "5. Below the section header, there is an explanatory text: 'Zdecyduj na jakich zasadach ma się wyświetlać tworzony przez Ciebie profil'"
        "6. There are two options for the user to choose from, each accompanied by a radio button allowing for a single selection:"
        "   - The first option is 'Profil publiczny' followed by a description 'Widoczny publicznie, każdy posiadający link lub skanujący QR Code może obejrzeć historię życia denata,' which refers to a publicly visible profile accessible to anyone with the link or scanning a QR code."
        "   - The second option is 'Profil prywatny' with a description 'Zabezpieczony hasłem dostępu, które zdecydujesz komu udostępnić,' implying that it is a private profile protected by a password, with user-controlled access."
        "7. At the bottom, there is a primary action button labeled 'Przejdź dalej' with an arrow indicating the direction to the next step. This button is likely meant to take the user to the next step in the process once they have made their selection regarding the profile's visibility."
        "The design of the page is clean and minimalist, with ample white space for clarity, and focused on guiding the user through the decision-making process for profile visibility settings."
        "'''")

file_contents = research_task(task)

planer = Planer(task, file_contents)
plan = planer.plan()

do_task(task, plan, file_contents)
