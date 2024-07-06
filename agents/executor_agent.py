import os
from tools.tools import see_file, replace_code, insert_code, create_file_with_code, ask_human_tool
from tools.tools import WRONG_EXECUTION_WORD
from langchain_openai.chat_models import ChatOpenAI
from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.graph import StateGraph
from dotenv import load_dotenv, find_dotenv
from langchain.tools.render import render_text_description
from langchain.tools import tool
from langchain_community.chat_models import ChatOllama
from langchain_anthropic import ChatAnthropic
from utilities.util_functions import check_file_contents, print_wrapped, check_application_logs, find_tool_json
from utilities.langgraph_common_functions import call_model, call_tool, ask_human, after_ask_human_condition
from langchain_groq import ChatGroq
from langchain_together import ChatTogether


load_dotenv(find_dotenv())
log_file_path = os.getenv("LOG_FILE")


@tool
def final_response():
    """Call that tool when all changes are implemented to tell the job is done. If you have no idea which tool to call,
    call that."""
    pass


tools = [see_file, insert_code, replace_code, create_file_with_code, ask_human_tool, final_response]
rendered_tools = render_text_description(tools)

stop_sequence = "\n```\n"

#llm = ChatOpenAI(model="gpt-4o", temperature=0).with_config({"run_name": "Executor"})
#llm = ChatAnthropic(model='claude-3-opus-20240229', temperature=0, max_tokens=1500, model_kwargs={"stop_sequences": [stop_sequence]}).with_config({"run_name": "Executor"})
llm = ChatAnthropic(model='claude-3-5-sonnet-20240620', temperature=0.2, max_tokens=1500, model_kwargs={"stop_sequences": [stop_sequence]}).with_config({"run_name": "Executor"})
#llm = ChatGroq(model="llama3-70b-8192", temperature=0).with_config({"run_name": "Executor"})
#llm = ChatTogether(model="meta-llama/Llama-3-70b-chat-hf", temperature=0).with_config({"run_name": "Executor"})
#llm = ChatOllama(model="mixtral"), temperature=0).with_config({"run_name": "Executor"})


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]


tool_executor = ToolExecutor(tools)
system_message = SystemMessage(
        content=f"""
You are a senior programmer tasked with refining an existing codebase. Your goal is to incrementally 
introduce improvements using a set of provided tools. Each change should be implemented step by step, 
meaning you make one modification at a time. Focus on enhancing individual functions or lines of code 
rather than rewriting entire files at once.
\n\n
Tools to your disposal:\n
{rendered_tools}
\n\n
First, write your thinking process. Think step by step about what do you need to do to accomplish the task. 
Next, call tool using template. Use only one json at once! If you want to introduce few changes, just choose one of them; 
rest will be possibility to do later.
```json
{{
    "tool": "$TOOL_NAME",
    "tool_input": "$TOOL_PARAMS",
}}
```
"""
    )

bad_json_format_msg = """Bad json format. Json should be enclosed with '```json', '```' tags.
Code inside of json should be provided in the way that not makes json invalid."""

class Executor():
    def __init__(self, files):
        self.files = files

        # workflow definition
        executor_workflow = StateGraph(AgentState)

        executor_workflow.add_node("agent", self.call_model_executor)
        #executor_workflow.add_node("checker", self.call_model_checker)
        executor_workflow.add_node("tool", self.call_tool_executor)
        executor_workflow.add_node("check_log", self.check_log)
        executor_workflow.add_node("human", ask_human)

        executor_workflow.set_entry_point("agent")

        #executor_workflow.add_edge("agent", "checker")
        executor_workflow.add_edge("tool", "agent")
        executor_workflow.add_conditional_edges("agent", self.after_agent_condition)
        executor_workflow.add_conditional_edges("check_log", self.after_check_log_condition)
        executor_workflow.add_conditional_edges("human", after_ask_human_condition)

        self.executor = executor_workflow.compile()

    # node functions
    def call_model_executor(self, state):
        #stop_sequence = None
        state, response = call_model(state, llm, stop_sequence_to_add=stop_sequence)
        # safety mechanism for a bad json
        tool_call = response.tool_call
        if tool_call is None or "tool" not in tool_call:
            state["messages"].append(HumanMessage(content=bad_json_format_msg))
            print("\nBad json provided, asked to provide again.")
        elif tool_call == "Multiple jsons found.":
            state["messages"].append(HumanMessage(content="You written multiple jsons at once. If you want to execute multiple "
                                                 "actions, choose only one for now; rest you can execute later."))
            print("\nToo many jsons provided, asked to provide one.")
        elif tool_call == "No json found in response.":
            state["messages"].append(HumanMessage(content="Good. Please provide a json tool call to execute an action."))
            print("\nNo json provided, asked to provide one.")
        return state

    def call_tool_executor(self, state):
        last_ai_message = state["messages"][-1]
        state = call_tool(state, tool_executor)
        if last_ai_message.tool_call["tool"] == "create_file_with_code":
            self.files.add(last_ai_message.tool_call["tool_input"]["filename"])
        if last_ai_message.tool_call["tool"] in ["insert_code", "replace_code", "create_file_with_code"]:
            # marking messages if they haven't introduced changes
            if last_ai_message.content.startswith(WRONG_EXECUTION_WORD):
                # last tool response message
                state["messages"][-1].to_remove = True
            else:
                state = self.exchange_file_contents(state)
            # checking if we have at least 3 "to_remove" messages in state and then calling human
            if len([msg for msg in state["messages"] if hasattr(msg, "to_remove")]) >= 3:
                # remove all messages (with and without "to_remove") since first "to_remove" message
                state["messages"] = state["messages"][:state["messages"].index([msg for msg in state["messages"] if hasattr(msg, "to_remove")][0])]
                human_input = input("Please suggest AI how to introduce that change correctly:")
                state.append(HumanMessage(content=human_input))

        return state

    def check_log(self, state):
        # Add logs
        logs = check_application_logs()
        log_message = HumanMessage(content="Logs:\n" + logs)

        state["messages"].append(log_message)
        return state

    # Conditional edge functions
    def after_agent_condition(self, state):
        last_message = state["messages"][-1]

        if last_message.content == bad_json_format_msg:
            return "agent"
        elif last_message.tool_call["tool"] != "final_response":
            return "tool"
        else:
            return "check_log" if log_file_path else "human"

    def after_check_log_condition(self, state):
        last_message = state["messages"][-1]

        if last_message.content.endswith("Logs are correct"):
            return "human"
        else:
            return "agent"

    # just functions
    def exchange_file_contents(self, state):
        # Remove old one
        state["messages"] = [msg for msg in state["messages"] if not hasattr(msg, "contains_file_contents")]
        # Add new file contents
        file_contents = check_file_contents(self.files)
        file_contents_msg = HumanMessage(content=f"File contents:\n{file_contents}", contains_file_contents=True)
        state["messages"].append(file_contents_msg)
        return state

    def do_task(self, task, plan, file_contents):
        print("Executor starting its work")
        inputs = {"messages": [
            system_message,
            HumanMessage(content=f"Task: {task}\n\n###\n\nPlan: {plan}"),
            HumanMessage(content=f"File contents: {file_contents}", contains_file_contents=True)
        ]}
        self.executor.invoke(inputs, {"recursion_limit": 150})["messages"][-1]


if __name__ == "__main__":
    task = """Your task is to create a Galerry page of the memorial profile. Use design prepared by designer.
Take a look at education page to make your code consistent with it.
"""
    plan = """To create a Gallery page for the memorial profile that is consistent with the existing EducationPage.vue and adheres to the design provided, follow this
complete plan:

1. **Create a new Vue component for the Gallery page**:
   - Create a new file named `GalleryPage.vue` in the `src/views/MemorialProfilePages/` directory.

2. **Define the template structure in `GalleryPage.vue`**:
   - Use the design as a reference to create the HTML structure with a header and a gallery grid.

3. **Add styles to `GalleryPage.vue`**:
   - Write SCSS/CSS to match the design, focusing on the layout of images and the header.

4. **Add the script section in `GalleryPage.vue`**:
   - Define a `props` object to receive the gallery data from the parent component.
   - Use the `apiUrl` to construct the full image URLs.

5. **Integrate the Gallery page into the main `MemorialProfile.vue`**:
   - Import the `GalleryPage` component.
   - Add the `GalleryPage` component to the `components` object.
   - Use a conditional statement to render the `GalleryPage` component if gallery items exist.

6. **Update the `MemorialProfile.vue` to pass the gallery data to the `GalleryPage` component**:
   - Find the section with the key 'gallery' and pass its items to the `GalleryPage` component as a prop.

Here is the detailed code for each step:

### Step 1: Create GalleryPage.vue
Create the file `src/views/MemorialProfilePages/GalleryPage.vue`.

### Step 2: Define the template structure
```vue
<template>
  <div class="gallery-page-container">
    <div class="header">
      <span class="icon">🖼️</span>
      <div class="title small-text">Galeria</div>
    </div>
    <div class="gallery-grid">
      <img v-for="imageUrl in galleryData.items" :key="imageUrl" :src="apiUrl + imageUrl.replace(/\\/g, '/')" alt="Gallery Image" class="gallery-item"/>
    </div>
  </div>
</template>
```

### Step 3: Add styles
```scss
<style lang="scss" scoped>
@import '@/assets/scss/MemorialProfile.scss';

.header {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 16px;
}

.gallery-grid {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.gallery-item {
  width: 100%;
  max-width: 600px;
  margin-bottom: 16px;
  object-fit: cover;
  border-radius: 8px;
}
</style>
```

### Step 4: Add the script section
```vue
<script>
export default {
  name: 'GalleryPage',
  props: {
    galleryData: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      apiUrl: process.env.VUE_APP_API_URL
    };
  }
};
</script>
```

### Step 5: Integrate GalleryPage into MemorialProfile.vue
```vue
<script>
// ... existing imports ...
import GalleryPage from '@/views/MemorialProfilePages/GalleryPage.vue';

export default {
  components: {
    // ... existing components ...
    GalleryPage
  },
  // ... existing data, methods, etc. ...
};
</script>
```

### Step 6: Update MemorialProfile.vue to pass gallery data
```vue
<template>
  <!-- ... existing code ... -->
  <GalleryPage
    v-if="(post.sections || []).find(section => section.key === 'gallery')?.items?.length > 0"
    :gallery-data="(post.sections || []).find(section => section.key === 'gallery')"
  />
  <!-- ... existing code ... -->
</template>
```

With these steps, you will have a Gallery page that displays all images from the gallery section of the JSON data, styled according to the provided design, and
integrated into the existing `MemorialProfile.vue`.
"""
    file_contents = """Files:
src/views/MemorialProfilePages/EducationPage.vue:

1|<template>
2|  <div class="profile-page-container">
3|    <div class="header">
4|      <span class="icon">🎓</span>
5|      <div class="title small-text">Edukacja</div>
6|    </div>
7|    <div>
8|      <img :src="apiUrl + educationData.photoUrl.replace(/\\/g, '/')" alt="Education Photo" class="photo-frame"/>
9|    </div>
10|    <h2 class="big-text">{{ educationData.startYear }} - {{ educationData.endYear }}</h2>
11|    <p class="small-text">{{ educationData.description }}</p>
12|    <div class="location-arrow">
13|      <span class="icon">👇</span>
14|    </div>
15|    <div class="location-name small-text">{{ educationData.place }}</div>
16|  </div>
17|</template>
18|
19|<script>
20|export default {
21|  name: 'EducationPage',
22|  props: {
23|    educationData: {
24|      type: Object,
25|      required: true
26|    }
27|  },
28|  data() {
29|    return {
30|      apiUrl: process.env.VUE_APP_API_URL
31|    };
32|  }
33|};
34|</script>
35|
36|<style lang="scss" scoped>
37|@import '@/assets/scss/MemorialProfile.scss';
38|
39|.profile-page-container {
40|  background-image: url('@/assets/images/profile_education_background.png');
41|  padding-top: 8px; /* Reduced padding to decrease space at the top */
42|}
43|
44|.header .icon {
45|  font-size: 24px;
46|}
47|
48|.title {
49|  margin-top: 8px;
50|  // Inherits small-text styles from profile.scss
51|}
52|
53|.photo-frame {
54|  margin-top: 16px;
55|  border: 1px solid #000;
56|  height: 16rem; /* Further reduced height */
57|  display: flex;
58|  justify-content: center;
59|  align-items: center;
60|}
61|
62|
63|.location-arrow .icon {
64|  font-size: 24px; // Adjust size as needed
65|  display: block; // Ensure the icon is centered
66|  margin: 16px auto; // Center the icon horizontally and add some margin
67|}
68|
69|.location-name {
70|  margin-top: 8px;
71|  // Inherits small-text styles from profile.scss
72|}
73|
74|/* Additional styles can be added as needed to match the design */
75|</style>


###

src/assets/scss/MemorialProfile.scss:

1|.profile-page-container {
2|  padding: 20px;
3|  background-color: #f5f5f5;
4|  height: 100vh;
5|  display: flex;
6|  flex-direction: column;
7|  justify-content: center;
8|  align-items: center;
9|  text-align: center;
10|  max-width: 600px;
11|  margin: 0 auto;
12|  overflow-x: hidden; /* Prevent horizontal scroll */
13|  font-family: 'Source Serif 4', serif;
14|}
15|
16|.small-text {
17|  font-size: 16px;
18|  color: gray;
19|  margin-bottom: 8px;
20|}
21|
22|.big-text {
23|  font-size: 48px;
24|  font-weight: 600;
25|  margin-top: 10px;
26|  margin-bottom: 10px;
27|}
28|
29|.btn-history,
30|.btn-return {
31|  margin-top: 32px; /* Adjusted to match the design */
32|  padding: 12px 16px; /* Adjusted to match the design */
33|  font-size: 0.875rem; /* Adjusted to 16px as per new requirement */
34|  background-color: #fff; /* Assuming button background from the design */
35|  line-height: 150%;
36|  color: #404040; /* Assuming button text color from the design */
37|  border: 2px solid #A3A3A3; /* Assuming button border from the design */
38|  border-radius: 25px; /* Rounded corners as in the image */
39|  box-shadow: none; /* Assuming no shadow from the design */
40|  font-weight: 400;
41|  display: flex;
42|  gap: 4px;
43|
44|  .icon {
45|    color: #404040;
46|  }
47|}


###

src/views/MemorialProfile.vue:

1|<template>
2|  <div>
3|    <div class="scroll-container">
4|      <CoverPage :profile-data="post" @scroll-to-second-page="handleScrollToSecondPage"/>
5|      <SecondPage :profile-data="post"/>
6|      <EducationPage
7|          v-for="educationItem in (post.sections || []).find(section => section.key === 'education')?.items || []"
8|          :key="educationItem.id"
9|          :education-data="educationItem"
10|      />
11|      <AchievementsPage
12|        :achievement-items="(post.sections || []).find(section => section.key === 'achievements')?.items || []"
13|        v-if="(post.sections || []).find(section => section.key === 'achievements')?.items.length > 0"
14|      />
15|      <WorkPage
16|        v-if="(post.sections || []).find(section => section.key === 'work')?.items?.length > 0"
17|        :work-data="(post.sections || []).find(section => section.key === 'work')?.items[0] || {}"
18|      />
19|      <AdditionalDescriptionPage
20|        v-for="additionalDescriptionItem in (post.sections || []).find(section => section.key === 'additional_description')?.items || []"
21|        :key="additionalDescriptionItem.id"
22|        :additional-description-data="additionalDescriptionItem"
23|      />
24|      <FamilyPage v-if="(post.sections || []).find(section => section.key === 'family')?.items?.length > 0" :family-data="(post.sections || []).find(section => section.key === 'family')?.items || []"/>
25|      <HobbyesPage
26|        :hobby-items="(post.sections || []).find(section => section.key === 'interests')?.items || []"
27|        v-if="(post.sections || []).find(section => section.key === 'interests')?.items.length > 0"
28|      />
29|      <ImportantEventsPage
30|        v-for="eventItem in (post.sections || []).find(section => section.key === 'important_events')?.items || []"
31|        :key="eventItem.id"
32|        :event-data="eventItem"
33|      />
34|      <FinalPage :profile-data="post" @scroll-to-top="handleScrollToTop"/>
35|    </div>
36|  </div>
37|</template>
38|
39|
40|<script>
41|import axios from 'axios';
42|import CoverPage from '@/views/MemorialProfilePages/CoverPage.vue';
43|import SecondPage from '@/views/MemorialProfilePages/SecondPage.vue';
44|import EducationPage from '@/views/MemorialProfilePages/EducationPage.vue';
45|import AchievementsPage from '@/views/MemorialProfilePages/AchievementsPage.vue';
46|import WorkPage from '@/views/MemorialProfilePages/WorkPage.vue';
47|import FinalPage from '@/views/MemorialProfilePages/FinalPage.vue';
48|import AdditionalDescriptionPage from '@/views/MemorialProfilePages/AdditionalDescriptionPage.vue';
49|import FamilyPage from '@/views/MemorialProfilePages/FamilyPage.vue';
50|import HobbyesPage from '@/views/MemorialProfilePages/HobbyesPage.vue';
51|import ImportantEventsPage from '@/views/MemorialProfilePages/ImportantEventsPage.vue';
52|
53|export default {
54|  components: {
55|    CoverPage,
56|    SecondPage,
57|    EducationPage,
58|    FamilyPage,
59|    FinalPage,
60|    AdditionalDescriptionPage,
61|    WorkPage,
62|    AchievementsPage,
63|    HobbyesPage,
64|    ImportantEventsPage,
65|  },
66|  data() {
67|    return {
68|      post: {
69|        title: '',
70|        description: '',
71|      },
72|      apiUrl: process.env.VUE_APP_API_URL,
73|      error: null,
74|    };
75|  },
76|  mounted() {
77|    this.fetchPost();
78|    this.setupScrollSnap();
79|  },
80|  methods: {
81|    async fetchPost() {
82|      try {
83|        const slotNumber = this.$route.params.slotNumber;
84|        const response = await axios.get(`${this.apiUrl}mem_profile/${slotNumber}`);
85|
86|        this.post = {
87|          ...this.post, // Spread existing properties
88|          ...response.data, // Spread response data
89|        };
90|      } catch (error) {
91|        console.error(error);
92|      }
93|    },
94|    setupScrollSnap() {
95|      const scrollContainer = document.querySelector('.scroll-container');
96|      scrollContainer.style.scrollSnapType = 'y mandatory';
97|      scrollContainer.style.overflowY = 'scroll';
98|      scrollContainer.style.height = '100vh';
99|      Array.from(scrollContainer.children).forEach(child => {
100|        child.style.scrollSnapAlign = 'start';
101|      });
102|    },
103|    handleScrollToTop() {
104|      const scrollContainer = document.querySelector('.scroll-container');
105|      scrollContainer.scrollTo({ top: 0, behavior: 'smooth' });
106|    },
107|    handleScrollToSecondPage() {
108|      const secondPageElement = document.querySelector('.second-page-class'); // Use the actual class or ID of the second page
109|      if (secondPageElement) {
110|        secondPageElement.scrollIntoView({ behavior: 'smooth' });
111|      }
112|    },
113|  },
114|};
115|</script>
116|
117|
118|<style scoped>
119|.scroll-container {
120|  height: 100vh; /* Full height of the viewport */
121|  overflow-y: scroll; /* Enable vertical scrolling */
122|  scroll-snap-type: y mandatory; /* Enable full section scroll snapping */
123|}
124|
125|.scroll-container > * {
126|  scroll-snap-align: start; /* Align children to the start */
127|}
128|</style>
"""
    files = set(["src/views/MemorialProfile.vue", "src/assets/scss/MemorialProfile.scss", "src/views/MemorialProfilePages/EducationPage.vue"])
    executor = Executor(files)
    executor.do_task(task, plan, file_contents)