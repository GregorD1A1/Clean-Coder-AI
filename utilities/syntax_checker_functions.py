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
        if code[i:i + open_tag_len] == open_tag and code[i + open_tag_len] in [' ', '>']:
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
  <div class="post-creation-page">
    <v-breadcrumbs :items="['Profil', 'Edycja profilu pamięci']"></v-breadcrumbs>

    <h1 class="steps-header">Edycja profilu pamięci</h1>

    <post-creation-step1
        v-if="currentStep === 1"
        :profile-data="profileData"
        @update:profile-data="setProfileData"
    ></post-creation-step1>
    <post-creation-step2
        v-if="currentStep === 2"
        :profile-data="profileData"
        @update:profile-data="setProfileData"
        @profile-image-uploaded="setProfileImageUrl"
        @profile-image-deleted="setProfileImageUrl(null)"
        @update:is-form-valid="setIsFormValid"
    ></post-creation-step2>
    <post-creation-step3
        v-if="currentStep === 3"
        :profile-data="profileData"
        @add-section="addSection"
        @add-section-item="addSectionItem"
        @remove-section="removeSection"
        @remove-section-item="removeSectionItem"
        @update-section-item-image="updateSectionItemImage"
        @remove-section-item-image="removeSectionItemImage"
        @gallery-images-updated="handleGalleryImagesUpdated"
    ></post-creation-step3>

    <div class="steps-footer">
      <v-btn
          v-if="currentStep !== 3"
          :disabled="isNextButtonDisabled"
          class="step-button"
          type="submit"
          @click="goToNextStep"
      >
        <span>Przejdź dalej</span>
        <v-icon>mdi-arrow-right</v-icon>
      </v-btn>

      <v-btn
          v-if="currentStep === 3"
          class="step-button"
          type="submit"
          @click="saveAndGoToPreview"
      >
        <span>Podgląd profilu</span>
        <v-icon>mdi-arrow-right</v-icon>
      </v-btn>

      <v-btn v-if="currentStep !== 1" class="step-button outline" @click="goToPreviousStep">
        <v-icon>mdi-arrow-left</v-icon>
        <span>Poprzedni krok</span>
      </v-btn>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import PostCreationStep1 from './PostCreationStep1.vue';
import PostCreationStep2 from './PostCreationStep2.vue';
import PostCreationStep3 from './PostCreationStep3.vue';
import {uuidv7} from "uuidv7";

export default {
  components: {
    PostCreationStep1,
    PostCreationStep2,
    PostCreationStep3,
  },
  data() {
    return {
      isFormValid: true,
      isNextButtonDisabled: false,
      apiUrl: process.env.VUE_APP_API_URL,
      currentStep: 1,
      profileData: {
        id: uuidv7(),
        isPrivate: false,
        firstName: '',
        secondName: '',
        lastName: '',
        familyName: '',
        birthDate: {
          day: '',
          month: '',
          year: '',
        },
        birthPlace: '',
        deathDate: {
          day: '',
          month: '',
          year: '',
        },
        deathPlace: '',
        mainPhotoUrl: '',
        sections: [],
      },
    };
  },
  mounted() {
    document.addEventListener("keyup", this.handleKeyUp);

    this.slotNumber = this.$route.params.slotNumber;

    if (this.slotNumber) {
      this.fetchProfileData(this.slotNumber);
    } else {
      this.setProfileData(this.profileData);
    }
  },
  unmounted() {
    document.removeEventListener("keyup", this.handleKeyUp);
  },
  methods: {
    handleKeyUp(event) {
      if (event.key === "Enter") {
        if (this.currentStep !== 3) {
          this.goToNextStep();
        } else {
          this.saveAndGoToPreview();
        }
      }
    },
    setIsFormValid(value) {
      this.isFormValid = value;
      this.setIsNextButtonDisabled(value);
    },
    fetchProfileData() {
      if (!this.slotNumber) {
        return;
      }

      axios.get(`${this.apiUrl}mem_profile/${this.slotNumber}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('userToken')}`
        }
      }).then((response) => {
        this.profileData = {
          id: response.data.id || '',
          isPrivate: response.data.isPrivate || false,
          firstName: response.data.firstName || '',
          secondName: response.data.secondName || '',
          lastName: response.data.lastName || '',
          familyName: response.data.familyName || '',
          birthDate: {
            day: response.data.birthDate?.day || '',
            month: response.data.birthDate?.month || '',
            year: response.data.birthDate?.year || '',
          },
          birthPlace: response.data.birthPlace || '',
          deathDate: {
            day: response.data.deathDate?.day || '',
            month: response.data.deathDate?.month || '',
            year: response.data.deathDate?.year || '',
          },
          deathPlace: response.data.deathPlace || '',
          mainPhotoUrl: response.data.mainPhotoUrl || '',
          sections: response.data.sections || [],
        };
      });
    },
    setProfileData(data) {
      if (!this.profileData) {
        return;
      }

      this.profileData = {...this.profileData, ...data};

      sessionStorage.setItem('profileId', JSON.stringify(this.profileData.id));
    },
    setIsNextButtonDisabled(isFormValid) {
      this.isNextButtonDisabled = this.currentStep === 2 && !isFormValid;
    },
    addSection(section) {
      if (!this.profileData) {
        return;
      }

      this.profileData.sections.push(section);

      this.save();
    },
    addSectionItem({category, newSectionItem}) {
      const sections = this.profileData.sections.map((section) => {
        if (section.id === category.id) {
          section.items.push(newSectionItem);
        }

        return section;
      });

      this.profileData = {
        ...this.profileData,
        sections,
      };

      this.save();
    },
    removeSection(sectionId) {
      if (!this.profileData) {
        return;
      }

      const filteredSections = this.profileData.sections.filter((section) => section.id !== sectionId);

      this.profileData = {
        ...this.profileData,
        sections: filteredSections,
      }
    },
    removeSectionItem(sectionId, itemId) {
      if (!this.profileData) {
        return;
      }

      this.profileData.sections = this.profileData.sections.map((section) => {
        if (section?.id === sectionId) {
          section.items = section.items.filter((item) => item?.id !== itemId);
        }

        return section;
      });
    },
    updateSectionItemImage(filePath, sectionId, itemId) {
      this.profileData.sections = this.profileData.sections.map((section) => {
        if (section.id === sectionId) {
          section.items = section.items.map((item) => {
            if (item.id === itemId) {
              item.photoUrl = filePath;
            }

            return item;
          });
        }

        return section;
      });

      this.save();
    },
    removeSectionItemImage(itemId) {
      this.profileData.sections = this.profileData.sections.map((section) => {
        section.items = section.items.map((item) => {
          if (item.id !== itemId) {
            return item;
          }

          item.photoUrl = '';
          return item;
        });

        return section;
      });

      this.save();
    },
    handleGalleryImagesUpdated(imagePaths) {
      this.profileData.sections = this.profileData.sections.map((section) => {
        if (section.key === 'gallery') {
          section.items = imagePaths;
        }

        return section;
      });

      this.save();
    },
    goToPreviousStep() {
      if (this.currentStep === 1) {
        return;
      }

      this.currentStep = this.currentStep - 1;
      this.setIsNextButtonDisabled(this.isFormValid);
    },
    goToNextStep() {
      this.currentStep = this.currentStep + 1;
      this.setIsNextButtonDisabled(this.isFormValid);
    },
    setProfileImageUrl(imageUrl) {
      if (!this.profileData) {
        return;
      }

      this.profileData.mainPhotoUrl = imageUrl || '';

      this.save();
    },
    saveAndGoToPreview() {
      this.save(true);
    },
    save(isPreview = false) {
      try {
        if (this.slotNumber) {
          this.updateProfile(isPreview);
        } else {
          this.createProfile(isPreview);
        }
      } catch (error) {
        console.error('Wystąpił błąd:', error);
        this.isError = true;
        this.errorMessage = 'Wystapił błąd. Spróbuj ponownie.';
      }
    },
    createProfile(isPreview) {
      axios.post(`${this.apiUrl}post_creation`, JSON.stringify(this.profileData), {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('userToken')}`
        }
      }).then((response) => {
        if (!isPreview) {
          return;
        }

        this.goToMemorialProfileView(response.data.slotNr);
      });
    },
    updateProfile(isPreview) {
      axios.put(`${this.apiUrl}mem_profile/${this.slotNumber}`, JSON.stringify(this.profileData), {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('userToken')}`
        }
      }).then(() => {
        if (!isPreview) {
          return;
        }

        this.goToMemorialProfileView(this.slotNumber);
      });
    },
    goToMemorialProfileView(slotNumber) {
      this.$router.push({name: 'memorial-profile-view', params: {slotNumber}});
    },
  },
};
</script>

<style lang="scss" scoped>
.post-creation-page {
  max-width: 600px;
  margin: 32px auto;
  padding: 20px;
  border-radius: 8px;
}

.footer {
  display: flex;
  justify-content: space-between;
}
</style>

"""

if __name__ == "__main__":
    print(parse_vue_basic(code))