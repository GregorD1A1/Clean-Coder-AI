import os
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langchain_anthropic import ChatAnthropic
from utilities.llms import llm_open_router
from utilities.start_work_functions import read_frontend_feedback_story
import base64
from langchain.output_parsers import XMLOutputParser
import textwrap
from playwright.sync_api import sync_playwright
from agents.file_answerer import ResearchFileAnswerer
from typing import Optional, List
from typing_extensions import Annotated, TypedDict
from pydantic import BaseModel, Field


llms = []
if os.getenv("ANTHROPIC_API_KEY"):
    llms.append(ChatAnthropic(
        model='claude-3-5-sonnet-20241022', temperature=0, max_tokens=2000, timeout=120
    ))
if os.getenv("OPENROUTER_API_KEY"):
    llms.append(llm_open_router("anthropic/claude-3.5-sonnet"))
if os.getenv("OPENAI_API_KEY"):
    llms.append(ChatOpenAI(model="gpt-4o", temperature=0, timeout=120))
if os.getenv("OLLAMA_MODEL"):
    llms.append(ChatOllama(model=os.getenv("OLLAMA_MODEL")))

llm = llms[0].with_fallbacks(llms[1:])

# read prompt from file
parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
with open(f"{parent_dir}/prompts/frontend_feedback_code_writing.prompt", "r") as f:
    prompt_template = f.read()
with open(f"{parent_dir}/prompts/frontend_feedback_scenarios_planning.prompt", "r") as f:
    scenarios_planning_prompt_template = f.read()


class ScreenshotDescriptionsStructure(BaseModel):
    """Output structure"""
    analysis: str = Field(description="""
1. Summarize the task given to the programmer
2. Break down the programmer's plan into key steps
3. Identify which steps potentially affect the frontend
4. List potential frontend elements that might be changed
5. Determine the minimum number of screenshots needed to verify the changes
6. Think if we can get rid of some of them
[Explain your thought process for each step]
""")
    questions: Optional[str] = Field(
        default=None,
        description="[List questions you have about missing information here.]"
    )
    screenshots: Optional[List[str]] = Field(default=None, description="""
['Clear instruction for the first screenshot', 'Clear instruction for the second screenshot, if needed', ...]
""")


class ScreenshotCodesStructure(BaseModel):
    """List of playwright codes"""
    screenshot_codes: List[str] = Field(description="""
Provide here your playwright codes for each screenshot.
""")


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


def write_screenshot_codes(task, plan, work_dir):
    story = read_frontend_feedback_story()
    story = story.format(frontend_port=os.environ["FRONTEND_PORT"])
    scenarios_planning_prompt = scenarios_planning_prompt_template.format(
        task=task,
        plan=plan,
        story=story,
    )
    llm_screenshot_descriptions = llm.with_structured_output(ScreenshotDescriptionsStructure).with_config({"run_name": "VFeedback_descriptions"})
    llm_screenshot_codes = llm.with_structured_output(ScreenshotCodesStructure).with_config({"run_name": "VFeedback_codes"})
    response = llm_screenshot_descriptions.invoke(scenarios_planning_prompt)
    questions = response.questions

    screenshot_descriptions = response.screenshots

    screenshots_descriptions_formatted = str(screenshot_descriptions)

    # fulfill the missing informations
    if questions:
        file_answerer = ResearchFileAnswerer(work_dir=work_dir)
        answers = file_answerer.research_and_answer(questions)
        screenshots_descriptions_formatted += f"\nAdditional info:\n{str(answers)}"

    codes_prompt = prompt_template.format(story=story, plan=plan, screenshots=screenshots_descriptions_formatted)

    playwright_codes = llm_screenshot_codes.invoke(codes_prompt)
    playwright_start = """
browser = p.chromium.launch(headless=False)
page = browser.new_page()
try:
"""
    playwright_end = """
    output = page.screenshot()
except Exception as e:
    output = f"{type(e).__name__}: {e}"
browser.close()
"""
    playwright_codes_list = []
    for playwright_code in playwright_codes.screenshot_codes:
        indented_playwright_code = textwrap.indent(playwright_code, '    ')
        code = playwright_start + indented_playwright_code + playwright_end
        playwright_codes_list.append(code)
    print(playwright_codes_list)
    return playwright_codes_list, screenshot_descriptions


def execute_screenshot_codes(playwright_codes_list, screenshot_descriptions):
    output_message_content = []
    p = sync_playwright().start()
    for i, code in enumerate(playwright_codes_list):
        screenshot_description = screenshot_descriptions[i]
        code_execution_variables = {'p': p}
        exec(code, {}, code_execution_variables)
        screenshot_bytes = code_execution_variables["output"]
        if isinstance(screenshot_bytes, str):
            # in case of error instead of screenshot_bytes
            output_message_content.extend([{"type": "text", "text": screenshot_description}, {"type": "text", "text": screenshot_bytes}])
            continue

        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        output_message_content.extend([
            {"type": "text", "text": f"See the screenshot with description:{screenshot_description}"},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{screenshot_base64}",
                },
            },
        ])

    return HumanMessage(content=output_message_content, contains_screenshots=True)


if __name__ == "__main__":
    codes = ["""
browser = p.chromium.launch(headless=False)
page = browser.new_page()
try:
    # Go to campaign profile page
    page.goto('http://localhost:5173/campaign/6b97b572-3714-4859-8794-1d211d57f513', timeout=10000)

    # Wait for the profile content to be fully loaded
    page.wait_for_load_state('networkidle')
    output = page.screenshot()
except Exception as e:
    output = f"{type(e).__name__}: {e}"
browser.close()
""", """
browser = p.chromium.launch(headless=False)
page = browser.new_page()
try:
    # Login as campaign user
    page.goto('http://localhost:5173/login')
    page.fill('input[type="email"]', 'frontend.feedback@campaign')
    page.fill('input[type="password"]', '123')
    page.click('button[type="submit"]')
    page.wait_for_url('**/')
    page.wait_for_load_state('networkidle')
    
    # Navigate to campaign profile page
    # Note: Using a known UUID for the test campaign profile
    page.goto('http://localhost:5173/campaign/test-campaign-uuid')
    
    # Wait for the profile content to load
    page.wait_for_selector('.campaign-profile')
    page.wait_for_selector('.campaign-details')
    
    # Ensure all dynamic content is loaded
    page.wait_for_load_state('networkidle')
    output = page.screenshot()
except Exception as e:
    output = f"{type(e).__name__}: {e}"
browser.close()
"""]

    execute_screenshot_codes(codes, ["scr1", "scr2"])
