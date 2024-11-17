import json
import re
import json5
import textwrap
from termcolor import colored
from rich.panel import Panel
from rich.syntax import Syntax
from rich.console import Console
from rich.padding import Padding
from pygments.util import ClassNotFound
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename


def split_text_and_code(text):
    pattern = r'```(\w+)\s*\n(.*?)\n\s*```'
    parts = re.split(pattern, text, flags=re.DOTALL)
    result = []
    for i, part in enumerate(parts):
        if i == 0 or i % 3 == 0:  # Text parts
            if parts[i].strip():
                result.append(('text', parts[i].strip()))
        elif i % 3 == 1:  # Code block or snippets parts
            language = parts[i]
            content = parts[i + 1]
            result.append(('snippet_or_tool', language, content.strip()))

    return result


def parse_tool_json(text):
    try:
        return json5.loads(text)
    except ValueError:
        return None


def print_formatted_content(content):
    content_parts = split_text_and_code(content)

    for part in content_parts:
        if part[0] == 'text':
            print_formatted(content=part[1], color="dark_grey")
        elif part[0] == 'snippet_or_tool':
            language = part[1]
            code_content = part[2]
            if language == 'json5':    # tool call
                json_data = parse_tool_json(code_content)
                if not json_data:
                    print_formatted("Badly parsed tool json:")
                    print_code_snippet(code=code_content, extension="json5")
                    return
                tool = json_data.get('tool')
                tool_input = json_data.get('tool_input', {})
                print_tool_message(tool_name=tool, tool_input=tool_input)
            else:       # code snippet
                print_code_snippet(code=code_content, extension=language)


def print_formatted(content, width=None, color=None, on_color=None, bold=False, end='\n'):
    if width:
        lines = content.split('\n')
        lines = [textwrap.fill(line, width=width) for line in lines]
        content = '\n'.join(lines)
    if bold:
        content = f"\033[1m{content}\033[0m"
    if color:
        content = colored(content, color, on_color=on_color, force_color=True)

    print(content, end=end)


def get_lexer(extension):
    try:
        lexer = get_lexer_by_name(extension)
    except ClassNotFound:
        if extension in ['tsx', 'vue', 'svelte']:
            lexer = get_lexer_by_name('jsx')
        else:
            lexer = get_lexer_by_name('text')
    return lexer


def print_code_snippet(code, extension, start_line=1, title=None):
    console = Console()

    lexer = get_lexer(extension)

    syntax = Syntax(
        code,
        lexer,
        line_numbers=True,
        start_line=start_line,
        theme="monokai",
        word_wrap=True,
        padding=(1, 1),
    )

    snippet_title = title or f"{extension.capitalize()} Snippet"
    if len(snippet_title) > 100:
        snippet_title = f"..{snippet_title[-95:]}"

    styled_code = Panel(
        syntax,
        border_style="bold yellow",
        title=snippet_title,
        expand=False
    )
    console.print(Padding(styled_code, 1))


def print_error(message: str) -> None:
    print_formatted(content=message, color="red", bold=False)


def print_tool_message(tool_name, tool_input=None):
    if tool_name == 'ask_human':
        pass
    elif tool_name == 'see_file':
        message = "Looking at the file content..."
        print_formatted(content=message, color='blue', bold=True)
        print_formatted(content=tool_input, color='cyan', bold=True)
    elif tool_name == 'list_dir':
        message = "Listing files in a directory..."
        print_formatted(content=message, color='blue', bold=True)
        print_formatted(content=tool_input, color='cyan', bold=True)
    elif tool_name == 'create_file_with_code':
        message = "Let's create new file..."
        extension = tool_input['filename'].split(".")[-1]
        print_formatted(content=message, color='blue', bold=True)
        print_code_snippet(code=tool_input['code'], extension=extension, title=tool_input['filename'])
    elif tool_name == 'insert_code':
        message = f"Let's insert code after line {tool_input['start_line']}"
        extension = tool_input['filename'].split(".")[-1]
        print_formatted(content=message, color='blue', bold=True)
        print_code_snippet(code=tool_input['code'], extension=extension, start_line=tool_input['start_line'] + 1, title=tool_input['filename'])
    elif tool_name == 'replace_code':
        message = f"Let's insert code on the place of lines {tool_input['start_line']} to {tool_input['end_line']}"
        extension = tool_input['filename'].split(".")[-1]
        print_formatted(content=message, color='blue', bold=True)
        print_code_snippet(code=tool_input['code'], extension=extension, start_line=tool_input['start_line'], title=tool_input['filename'])

    elif tool_name == 'add_task':
        message = "Let's add a task..."
        print_formatted(content=message, color='blue', bold=True)
        print_code_snippet(code=tool_input['task_description'], title=tool_input['task_name'], extension='text')
    elif tool_name == 'create_epic':
        message = "Let's create an epic..."
        print_formatted(content=message, color='blue', bold=True)
        print_formatted(content=tool_input, color='cyan', bold=True)

    elif tool_name == 'final_response_researcher':
        json_string = json.dumps(tool_input, indent=2)
        print_code_snippet(code=json_string, extension='json', title='Files:')
    elif tool_name == 'final_response_executor':
        message = "Hurray! The work is DONE!"
        print_formatted(content=message, color='cyan', bold=True)
        if isinstance(tool_input, str):
            print_code_snippet(code=tool_input, extension='text', title='Instruction:')
        else:
            print_code_snippet(code=tool_input["test_instruction"], extension='text', title='Instruction:')
    elif tool_name == 'final_response_debugger':
        print_code_snippet(code=tool_input, extension='text', title='Instruction:')
        print_formatted("Have any questions about Clean Coder or want to share your experience? Check out our Discord server https://discord.com/invite/8gat7Pv7QJ 😉", color='green')
    else:
        message = f"Calling {tool_name} tool..."
        print_formatted(content=message, color='blue', bold=True)
        print_formatted(content=tool_input, color='blue', bold=True)


if __name__ == '__main__':
    code = """
<template>
  <Notification v-show="notificationMessage" :message="notificationMessage" :type="notificationType" />
  <div class="survey">
    <h1>Intern Survey</h1>
    <p>Welcome to the intern survey. Please fill out the form below.</p>
    <p class="notice">This survey is optional but highly suggested for competitiveness.</p>
    <p class="notice">The information will be presented on your profile page.</p>
    <form @submit.prevent="submitSurvey">
      <div v-for="(category, index) in surveyCategories" :key="index" class="survey-category">
        <h2>{{ category.name }}</h2>
        <div v-for="(statement, idx) in category.statements" :key="idx" class="survey-question">
          <label :for="statement.id">{{ statement.text }}</label>
          <div class="range-container">
            <input type="range" :id="statement.id" v-model="statement.value" min="1" max="5" step="1" :disabled="isSubmitted" @input="updateProgress">
          </div>
          <div class="scale-labels">
            <span class="scale-label left">Strongly Disagree</span>
            <span class="scale-label right">Strongly Agree</span>
          </div>
        </div>
      </div>
      <div class="bio-section">
        <label for="bio">Bio (300 words max):</label>
        <textarea id="bio" v-model="bio" placeholder="Provide here past experiences including education and previous relevant employment/internships/fellowships as well as hobbies, interests, areas of focus (comms, finance, data analytics) etc." :disabled="isSubmitted" maxlength="1500"></textarea>
      </div>
      <button type="submit" :disabled="isSubmitted">Submit Survey</button>

    </form>
  </div>
</template>
<script>
import Notification from '@/components/Notification.vue';
import { surveyCategories as initialSurveyCategories } from './SurveyCategories';
export default {
  data() {
    return {
      apiUrl: import.meta.env.VITE_API_URL,
      surveyCategories: initialSurveyCategories,
      bio: '',
      isSubmitted: false,
      notificationMessage: '',
      notificationType: 'positive',
    };
  },
  components: {
    Notification,
  },
  methods: {
    async submitSurvey() {
      console.log('Survey Data:', this.surveyCategories);
      console.log('Bio:', this.bio);
      
      const payload = {
        surveyData: this.surveyCategories,
        bio: this.bio,
      };
      
      console.log('body:', payload);
      
      try {
        const response = await fetch(`${this.apiUrl}/submit-survey`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
          body: JSON.stringify(payload),
        });
        
        const result = await response.json();
        if (response.ok) {
          console.log(result.message);
          this.notificationMessage = 'Survey saved successfully!';
          this.notificationType = 'positive';
          setTimeout(() => {
            this.notificationMessage = '';
            this.$router.push({ name: 'home' }); // Redirect to home page
          }, 2000);
        } else {
          console.error(result.detail);
        }
      } catch (error) {
        console.error('Error submitting survey:', error);
      }
    },


  }
};
</script>
<style scoped src="@/assets/styles/surveys.css"></style>

<style scoped>
.survey {
  max-width: 800px;
  margin: 0 auto;
  padding: 30px;
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e0e0e0;
}

h1 {
  font-size: 2.5em;
  color: #3498db;
  margin-bottom: 20px;
  text-align: center;
}

p {
  font-size: 1.1em;
  color: #555;
  margin-bottom: 20px;
  text-align: center;
}

.notice {
  font-style: italic;
  color: #7f8c8d;
  font-size: 0.9em;
  margin-bottom: 30px;
}

.survey-category {
  margin-bottom: 40px;
  background-color: #f9f9f9;
  padding: 25px;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  border: 1px solid #e0e0e0;
}

.survey-category h2 {
  font-size: 1.8em;
  color: #3498db;
  margin-bottom: 20px;
  border-bottom: 2px solid #3498db;
  padding-bottom: 10px;
}

.survey-question {
  margin-bottom: 30px;
}

label {
  display: block;
  margin-bottom: 12px;
  font-weight: 600;
  color: #2c3e50;
  font-size: 1.1em;
}

button {
  background-color: #3498db;
  color: white;
  padding: 14px 28px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.3s ease;
  margin-right: 15px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

button:hover:not(:disabled) {
  background-color: #2980b9;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
}

button:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.range-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
}

input[type="range"] {
  width: 100%;
  margin: 0;
  -webkit-appearance: none;
  appearance: none;
  height: 10px;
  border-radius: 5px;
  background: #e0e0e0;
  outline: none;
  opacity: 0.7;
  transition: opacity .2s;
}

input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3498db;
  cursor: pointer;
}

input[type="range"]::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3498db;
  cursor: pointer;
}

.scale-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  position: relative;
  font-size: 0.9em;
  color: #7f8c8d;
}

.scale-label {
  font-weight: bold;
  color: #3498db;
  font-size: 1em;
  position: absolute;
}

.scale-label.left {
  text-align: left;
  left: 0;
}

.scale-label.right {
  text-align: right;
  right: 0;
}

.selected-value {
  text-align: center;
.bio-section {
  margin-top: 30px;
  text-align: left;
}

textarea {
  width: 100%;
  height: 150px;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 5px;
  resize: none;
  font-size: 1em;
  color: #2c3e50;
  margin-bottom: 10px;
}

textarea:disabled {
  background-color: #f0f0f0;
  margin-top: 10px;
  font-weight: bold;
  color: #3498db;
  font-size: 1em;
}
}
</style>    
"""
    print_code_snippet(code, "vue")