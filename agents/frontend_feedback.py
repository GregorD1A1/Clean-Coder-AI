import os
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from dotenv import load_dotenv, find_dotenv
from langchain.tools import tool
from langchain_community.chat_models import ChatOllama
from langchain_anthropic import ChatAnthropic
from utilities.llms import llm_open_router
from utilities.print_formatters import print_formatted
from utilities.start_project_functions import read_frontend_feedback_story
from utilities.util_functions import (
    check_file_contents, check_application_logs, render_tools, find_tools_json
)
from langchain.output_parsers import XMLOutputParser


llms = []
if os.getenv("ANTHROPIC_API_KEY"):
    llms.append(ChatAnthropic(
        model='claude-3-5-haiku-20241022', temperature=0, max_tokens=2000, timeout=120
    ).with_config({"run_name": "VFeedback"}))
if os.getenv("OPENROUTER_API_KEY"):
    llms.append(llm_open_router("anthropic/claude-3.5-haiku").with_config({"run_name": "VFeedback"}))
if os.getenv("OPENAI_API_KEY"):
    llms.append(ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=120).with_config({"run_name": "VFeedback"}))
if os.getenv("OLLAMA_MODEL"):
    llms.append(ChatOllama(model=os.getenv("OLLAMA_MODEL")).with_config({"run_name": "VFeedback"}))

llm = llms[0].with_fallbacks(llms[1:])

story = read_frontend_feedback_story()
story = story.format(frontend_port=5173)

# read prompt from file
parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
with open(f"{parent_dir}/prompts/frontend_feedback.prompt", "r") as f:
    prompt_template = f.read()

task = """Create Page for Intern Profile Editing
1. Implement a new page in the frontend where interns can update their profile information.
2. Ensure this page is accessible from the user's dashboard or profile section.
3. Include fields for editing the full name, political affiliation (predefined select), start and end dates (using a datepicker), and active search status (toggle switch).
4. Use step 2 of the registration page as a reference for design and functionality.
5. Ensure that changes made on this page are sent to the backend to update the intern's profile in the 'interns' collection.

Definition of Done:
- A dedicated page for intern profile editing is implemented.
- Fields for editing the specified information are included, using the registration page as a reference.
- Changes are successfully sent to the backend for processing.
"""

plan = """### Plan for Implementing Intern Profile Editing Page

#### Frontend Modifications

1. **Create a New Vue Component for Profile Editing**

   - **File**: `Glovn_Frontend/src/views/profile/InternProfileEdit.vue` (New File)
   - **Content**:
     ```vue
     <template>
       <div class="form-container">
         <Notification v-show="notificationMessage" :message="notificationMessage" :type="notificationType" />
         <h1>Edit Profile</h1>
         <form @submit.prevent="handleProfileUpdate">
           <div>
             <label for="fullName">Full Name:</label>
             <input type="text" v-model="fullName" required />
           </div>
           <div>
             <label for="politicalAffiliation">Political Affiliation:</label>
             <select v-model="politicalAffiliation" required>
               <option value="democrat">Democrat</option>
               <option value="republican">Republican</option>
             </select>
           </div>
           <div>
             <label for="startDate">Available From:</label>
             <input type="date" v-model="startDate" :min="today" required />
           </div>
           <div>
             <label for="endDate">Available Until:</label>
             <input type="date" v-model="endDate" :min="today" :disabled="noEndDate" required />
             <div class="checkbox-container">
               <input type="checkbox" id="noEndDate" v-model="noEndDate" />
               <label for="noEndDate"> No End Date</label>
             </div>
           </div>
           <div>
             <label for="activeSearch">Active Search:</label>
             <input type="checkbox" v-model="activeSearch" />
           </div>
           <button type="submit">Update Profile</button>
         </form>
       </div>
     </template>

     <script>
     import Notification from '@/components/Notification.vue';
     import { useAuthStore } from '@/stores/auth';

     export default {
       components: {
         Notification,
       },
       data() {
         return {
           fullName: '',
           politicalAffiliation: '',
           startDate: '',
           endDate: '',
           noEndDate: false,
           activeSearch: false,
           apiUrl: import.meta.env.VITE_API_URL,
           notificationMessage: '',
           notificationType: 'positive',
         };
       },
       computed: {
         today() {
           return new Date().toISOString().split('T')[0];
         },
       },
       created() {
         const authStore = useAuthStore();
         if (!authStore.isLoggedIn) {
           this.$router.push('/login');
         } else {
           this.loadProfile();
         }
       },
       methods: {
         async loadProfile() {
           // Fetch current profile data from backend
           // Populate data properties with fetched data
         },
         async handleProfileUpdate() {
           const payload = {
             fullName: this.fullName,
             politicalAffiliation: this.politicalAffiliation,
             startDate: this.startDate,
             endDate: this.noEndDate ? null : this.endDate,
             activeSearch: this.activeSearch,
           };
           try {
             const response = await fetch(this.apiUrl + '/profile/intern', {
               method: 'PUT',
               headers: {
                 'Content-Type': 'application/json',
                 'Authorization': `Bearer ${localStorage.getItem('token')}`
               },
               body: JSON.stringify(payload),
             });
             if (!response.ok) {
               throw new Error('Profile update failed');
             }
             this.notificationMessage = 'Profile updated successfully';
             this.notificationType = 'positive';
             setTimeout(() => {
               this.notificationMessage = '';
             }, 2000);
           } catch (error) {
             this.notificationMessage = error.message;
             this.notificationType = 'negative';
             setTimeout(() => {
               this.notificationMessage = '';
             }, 2000);
           }
         },
       },
     };
     </script>

     <style scoped src="@/assets/styles/forms.css"></style>
     <style scoped>
     .checkbox-container {
       display: block;
       align-items: center;
       gap: 0.5rem;
     }
     </style>
     ```

2. **Add Route for Profile Editing Page**

   - **File**: `Glovn_Frontend/src/router/index.js`
   - **Modifications**:
     ```diff
     + {
     +   path: '/profile/edit',
     +   name: 'profile-edit',
     +   component: () => import('../views/profile/InternProfileEdit.vue')
     + },
     ```

3. **Update Dashboard or Profile Section to Link to Profile Editing Page**

   - **File**: `Glovn_Frontend/src/views/HomeView.vue` (or appropriate dashboard file)
   - **Modifications**:
     ```html
     <template>
       <main>
         <!-- Existing content -->
         <router-link to="/profile/edit">Edit Profile</router-link>
       </main>
     </template>
     ```

#### Backend Modifications

1. **Create Endpoint for Updating Intern Profile**

   - **File**: `Glovn_Backend/main.py`
   - **Modifications**:
     ```diff
     + @app.put("/profile/intern")
     + async def update_intern_profile(request: Request, token: str = Depends(oauth2_scheme)):
     +     try:
     +         current_user = get_current_user(token)
     +     except HTTPException as e:
     +         raise HTTPException(
     +             status_code=status.HTTP_401_UNAUTHORIZED,
     +             detail=f"Authentication error: {str(e)}"
     +         )
     + 
     +     data = await request.json()
     +     full_name = data.get("fullName")
     +     political_affiliation = data.get("politicalAffiliation")
     +     start_date = data.get("startDate")
     +     end_date = data.get("endDate")
     +     active_search = data.get("activeSearch")
     + 
     +     interns_collection = db['interns']
     +     result = interns_collection.update_one(
     +         {"email": current_user['email']},
     +         {"$set": {
     +             "full_name": full_name,
     +             "political_affiliation": political_affiliation,
     +             "start_date": start_date,
     +             "end_date": end_date,
     +             "active_search": active_search
     +         }}
     +     )
     + 
     +     if result.modified_count > 0:
     +         return {"message": "Profile updated successfully"}
     +     else:
     +         raise HTTPException(
     +             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
     +             detail="Failed to update profile"
     +         )
     ```

This plan outlines the necessary steps to create a new page for intern profile editing, ensuring that the changes are consistent with existing code and functionality.
"""


scenarios_planning_prompt_template = """You are the frontend visual tester.
You helping a programmer that creates new frontend feature to see if changes he implemented work by providing a screenshots of application.

Your task is to think what screenshots needed to be provided to programmer in order to make him understand if change been implemented correctly.
Provide as less screenshots as possible (only that really needed).

Do not care about different layout sizes (as mobile).

If you don't know some needed information, as endpoint name or element selectors, never imagine it or use placeholders; instead, ask on the end of your response in the <questions> field.
Although, never ask questions if answer is provided in the plan. You will be penalized for asking not necessary questions.
Write 'Everything clear.' inside of <questions></questions> if you have no questions.
###
Example 1:
<task_given_to_programmer>
Update contact information page with fax information.
</task_given_to_programmer>
<plan_of_programmers_actions>
here is a code we need to add to contact page:
```vue
<code with fax here>
```
also update router file:
```js
<code with router of contact page, showing page placed under /contact endpoint>
```
</plan_of_programmers_actions>

Your output:
'''
<response>
<reasoning>
In order to test update of contact page, we need to go to the /contact endpoint and make screenshot here to veryfy if contact page has fax available on it.
<reasoning>
<screenshots>
<screenshot_1>
Go to /contact endpoint and make screenshot.
</screenshot_1>
</screenshots>
<questions>
Everything clear.
</questions>
</response>
'''
###
Example 2:
<task_given_to_programmer>
Make 'about us' page more prettier.
</task_given_to_programmer>
<plan_of_programmers_actions>
here is a code we need to update 'about us' page with:
```vue
<code diff here>
```
</plan_of_programmers_actions>

Your output:
'''
<response>
<reasoning>
In order to test update of 'about us' page, we need to go to it and make screenshot. However, we don't have any information about name of it's endpoint.
<reasoning>
<screenshots>
<screenshot_1>
Endpoint name of 'about us' page need to be figuring out before going here and making screenshot.
</screenshot_1>
</screenshots>
<questions>
1. Provide an endpoint name of 'about us' page.
</questions>
</response>
'''
###
Example 3:
<task_given_to_programmer>
Create new page with user survey. Should be available only for logged in users.
</task_given_to_programmer>
<plan_of_programmers_actions>
Create new page with survey under /survey-page endpoint. verification is required.
```vue
<code of survey page here>
```
</plan_of_programmers_actions>

Your output:
'''
<response>
<reasoning>
In order to test creating of survey page, we need to log in go to the /survey-page endpoint and make screenshot to veryfy if survey page exists and looks as intended. Also, we need to go to /survey-page endpoint without login and confirm it is not accessible.
</reasoning>

<screenshots>
<screenshot_1>
Log in, then go to /survey-page endpoint and make screenshot.
</screenshot_1>
<screenshot_2>
Go to /survey-page endpoint without login and also make screenshot to confirm it is not accessible.
</screenshot_2>
</screenshots>
<questions>
Everything clear.
</questions>
</response>
'''
###
Example 4:
<task_given_to_programmer>
Modify logic of backend registration, to separate normal users and admins.
</task_given_to_programmer>
<plan_of_programmers_actions>
Modify register_user function in registration.py with next code:
```python
some code here
```
</plan_of_programmers_actions>

Your output:
'''
<response>
<reasoning>
Provided change is related to the backend logic and does not affect frontend. Therefore, no screenshots required.
</reasoning>
<screenshots>
</screenshots>
<questions>
Everything clear.
</questions>
</response>
'''
###
Actual task and plan:
<task_given_to_programmer>
{task}
</task_given_to_programmer>

<plan_of_programmers_actions>
{plan}
</plan_of_programmers_actions>
"""

def debug_print(response):
    print(response.content)
    return response


def make_feedback_screenshots(task, plan):
    scenarios_planning_prompt = scenarios_planning_prompt_template.format(
        task=task,
        plan=plan,
    )
    xml_parser_chain = llm | debug_print | XMLOutputParser()
    scenarios = xml_parser_chain.invoke(scenarios_planning_prompt)
    screenshots = scenarios["response"][1]["screenshots"]

    screenshots_xml = ""
    for i, screenshot in enumerate(screenshots):
        screenshots_xml += f"<screenshot_{i+1}>{screenshot[f'screenshot_{i+1}']}</screenshot_{i+1}>\n"

    final_output_prompt = prompt_template.format(story=story, plan=plan, screenshots=screenshots_xml)

    playwright_codes = xml_parser_chain.invoke(final_output_prompt)["response"]
    playwright_start = """
from playwright.sync_api import sync_playwright

p = sync_playwright().start()
browser = p.chromium.launch(headless=False)
page = browser.new_page()
"""
    playwright_end = """
browser.close()
"""
    for i, playwright_code in enumerate(playwright_codes):
        playwright_code = playwright_code[f"screenshot_{i+1}"]
        code = playwright_start + playwright_code + playwright_end
        print(code)
        exec(code)


if __name__ == "__main__":
    make_feedback_screenshots(task, plan)
