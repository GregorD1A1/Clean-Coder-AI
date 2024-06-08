import ast
from bs4 import BeautifulSoup
import esprima
import sass
from lxml import etree
import re


def check_syntax(file_content, filename):
    parts = filename.split(".")
    extension = parts[-1] if len(parts) > 1 else ''
    if extension == "py":
        return parse_python(file_content)
    elif extension in ["html", "htm"]:
        return parse_html(file_content)
    elif extension == "js":
        return parse_javascript(file_content)
    elif extension in ["css", "scss"]:
        return parse_scss(file_content)
    elif extension == "vue":
        return parse_vue_basic(file_content)
    else:
        return "Valid syntax"


def parse_python(code):
    try:
        ast.parse(code)
        return "Valid syntax"
    except SyntaxError as e:
        return f"Syntax Error: {e.msg} (line {e.lineno - 1})"
    except Exception as e:
        return f"Error: {e}"


def parse_html(html_content):
    parser = etree.HTMLParser(recover=True)  # Enable recovery mode
    try:
        html_tree = etree.fromstring(html_content, parser)
        significant_errors = [
            error for error in parser.error_log
            # Shut down some error types to be able to parse html from vue
            #if not error.message.startswith('Tag')
            #and "error parsing attribute name" not in error.message
        ]
        if not significant_errors:
            return "Valid syntax"
        else:
            for error in significant_errors:
                return f"HTML line {error.line}: {error.message}"
    except etree.XMLSyntaxError as e:
        return f"Html error occurred: {e}"


def parse_vue_template_part(code):
    for tag in ['div', 'p', 'span']:
        function_response = check_template_tag_balance(code, f'<{tag}', f'</{tag}>')
        if function_response != "Valid syntax":
            return function_response
    return "Valid syntax"


def parse_javascript(js_content):
    try:
        esprima.parseModule(js_content)
        return "Valid syntax"
    except esprima.Error as e:
        print(f"Esprima syntax error: {e}")
        return f"JavaScript syntax error: {e}"


def check_template_tag_balance(code, open_tag, close_tag):
    opened_tags_count = 0
    open_tag_len = len(open_tag)
    close_tag_len = len(close_tag)

    i = 0
    while i < len(code):
        # check for open tag plus '>' or space after
        if code[i:i + open_tag_len] == open_tag and code[i + open_tag_len] in [' ', '>', '\n']:
            opened_tags_count += 1
            i += open_tag_len
        elif code[i:i + close_tag_len] == close_tag:
            opened_tags_count -= 1
            i += close_tag_len
            if opened_tags_count < 0:
                return f"Invalid syntax, mismatch of {open_tag} and {close_tag}"
        else:
            i += 1

    if opened_tags_count == 0:
        return "Valid syntax"
    else:
        return f"Invalid syntax, mismatch of {open_tag} and {close_tag}"


def check_bracket_balance(code):
    opened_brackets_count = 0

    for char in code:
        if char == '{':
            opened_brackets_count += 1
        elif char == '}':
            opened_brackets_count -= 1
            if opened_brackets_count < 0:
                return "Invalid syntax, mismatch of { and }"

    if opened_brackets_count == 0:
        return "Valid syntax"
    else:
        return "Invalid syntax, mismatch of { and }"


def parse_scss(scss_code):
    # removing import statements as they cousing error, because function has no access to filesystem
    scss_code = re.sub(r'@import\s+[\'"].*?[\'"];', '', scss_code)

    try:
        sass.compile(string=scss_code)
        return "Valid syntax"
    except sass.CompileError as e:
       return f"CSS/SCSS syntax error: {e}"


# That function does not guarantee finding all the syntax errors in template and script part; but mostly works
def parse_vue_basic(content):
    start_tag_template = re.search(r'<template>', content).end()
    end_tag_template = content.rindex('</template>')
    template = content[start_tag_template:end_tag_template]
    template_part_response = parse_vue_template_part(template)
    if template_part_response != "Valid syntax":
        return template_part_response

    try:
        script = re.search(r'<script>(.*?)</script>', content, re.DOTALL).group(1)
    except AttributeError:
        return "Script part has no valid open/closing tags."
    script_part_response = check_bracket_balance(script)
    if script_part_response != "Valid syntax":
        return script_part_response

    style_match = re.search(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
    if style_match:
        style_part_response = parse_scss(style_match.group(1))
        if style_part_response != "Valid syntax":
            return style_part_response

    return "Valid syntax"

# Function under development
def lint_vue_code(code_string):
    import subprocess
    import os
    eslint_config_path = '.eslintrc.js'
    temp_file_path = "dzik.vue"
    # Create a temporary file
    with open(temp_file_path, 'w', encoding='utf-8') as file:
        file.write(code_string)
    try:
        # Run ESLint on the temporary file
        result = subprocess.run(['D:\\NodeJS\\npx.cmd', 'eslint', '--config', eslint_config_path, temp_file_path, '--fix'], check=True, text=True, capture_output=True)
        print("Linting successful:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error during linting:", e.stderr)
    finally:
        # Clean up by deleting the temporary file
        os.remove(temp_file_path)



code = """
<template>
  <div class="dashboard content">
    <div class="container">
      <h1 class="dashboard-title">Panel użytkownika</h1>

      <ul class="mem-profile-list">
        <li v-for="mem_profile in mem_profiles" :key="mem_profile.slot_number" class="mem-profile-item">
          <span class="mem-profile-name">
            {{ mem_profile.firstName }} {{ mem_profile.secondName }} {{ mem_profile.lastName }}</span>
          (Numer profilu: {{ mem_profile.slot_number }})
          <div class="button-container">
            <button class="edit-button" @click="editMemProfile(mem_profile.slot_number)">Edytuj</button>
            <button class="share-button" @click="copyProfileLink(mem_profile.slot_number)">Udostępnij</button>
            <span
                v-show="showTooltip && tooltipSlotNumber === mem_profile.slot_number"
                class="tooltip"
            >Link skopiowany</span>
            <button class="profile-button" @click="redirectToProfile(mem_profile.slot_number)">Zobacz profil</button>
          </div>
        </li>
      </ul>

      <button class="button create-button" @click="goToCreateMemProfile">Kup nowy profil</button>
    </div>
  </div>
</template>

<script>
import '@/assets/scss/common.scss';
import axios from 'axios';

export default {
  name: 'DashboardPage',
  data() {
    return {
      mem_profiles: [],
      apiUrl: process.env.VUE_APP_API_URL, // Ensure this is set in your .env file
      showTooltip: false,
      tooltipSlotNumber: null,
    };
  },
  async created() {
    await this.fetchMemProfiles();
  },
  methods: {
    async fetchMemProfiles() {
      try {
        const token = localStorage.getItem('userToken'); // Retrieve token from localStorage
        const response = await axios.get(`${this.apiUrl}dashboard/`, {
          headers: {
            'Authorization': `Bearer ${token}` // Use the token for authorization
          }
        });
        this.mem_profiles = response.data.mem_profiles;
      } catch (error) {
        console.error('Error fetching memorial profiles:', error);
      }
    },
    editMemProfile(slotNumber) {
      this.$router.push({name: 'memorial-profile-edit', params: {slotNumber: slotNumber}});
    },
    goToCreateMemProfile() {
      this.$router.push({name: 'create-mem-profile'});
    },
    copyProfileLink(slotNumber) {
      const link = `https://takzyli.pl/memorial_profile/${slotNumber}`;
      navigator.clipboard.writeText(link).then(() => {
        this.showTooltip = true;
        this.tooltipSlotNumber = slotNumber;
        setTimeout(() => {
          this.showTooltip = false;
          this.tooltipSlotNumber = null;
        }, 2000);
      }, (err) => {
        console.error('Could not copy text: ', err);
      });
    },
    redirectToProfile(slotNumber) {
      this.$router.push({path: `/memorial_profile/${slotNumber}`});
    },
  }
};
</script>

<style lang="scss" scoped>
.dashboard {
  padding: 20px;
  background-color: #f5f5f5;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.dashboard-title {
  font-size: 24px;
  margin-bottom: 20px;
}

.mem-profile-list {
  list-style-type: none;
  padding: 0;
}

.mem-profile-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin-bottom: 10px;
}

.mem-profile-name {
  font-weight: bold;
}

.edit-button, .create-button {
  width: 100%;
  background-color: black;
  color: white;
  border: none;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 5px; /* Rounded edges */
  font-weight: 600;
  transition: background-color 0.3s ease;
  align-self: center;

  @media (min-width: 768px) {
    width: fit-content;
  }
}

.edit-button {
  margin: 0 5px 5px;
}

.edit-button:hover, .create-button:hover {
  background-color: #333;
}

.share-button {
  color: DeepSkyBlue;
  border: 1px solid DeepSkyBlue;
  background-color: transparent;
  padding: 8px 16px;
  border-radius: 5px;
  font-weight: 600;
  transition: all 0.3s ease;
  margin: 0 5px 5px;
}

.share-button:hover {
  background-color: DeepSkyBlue;
  color: white;
}

.profile-button {
  background-color: #808080; // Gray color
  color: white;
  border: none;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 5px;
  font-weight: 600;
  transition: background-color 0.3s ease;
  margin: 0 5px 5px;
}

@media (max-width: 768px) {
  .mem-profile-item {
    flex-direction: column;
    align-items: center;
  }
  .edit-button, .share-button, .profile-button {
    width: calc(100% - 20px); /* Adjust width to allow for margin */
  }
}


.profile-button:hover {
  background-color: #696969; // Slightly darker shade on hover
}

.tooltip {
  position: absolute;
  top: -30px;
  right: 50%;
  transform: translateX(100%);
  background-color: gray;
  color: white;
  padding: 5px;
  border-radius: 5px;
  white-space: nowrap;
  font-size: 0.7em;
}

.button-container {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 5px;
}
</style>

"""

if __name__ == "__main__":
    print(parse_vue_basic(code))