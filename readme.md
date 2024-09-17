![Logo](./assets/logo_wide.png)
<div align="center">
<h2>Your 2-in-1 AI Scrum Master and Developer</h2>
</div>

Clean Coder: Your AI-powered software project assistant. Deligate planing, managing, and coding to AI. Agents break down tasks on Todoist, write code, and test themselves, helping you create great projects with minimal effort and stress!

### Relax and watch it code

```
# clone repo
git clone https://github.com/GregorD1A1/Clean-Coder-AI

# go to directory
cd Clean-Coder-AI

# install dependencies
pip install -r requirements.txt

# provide path to the project directory you'll work on
export WORK_DIR=/path/to/your/project/dir

# provide api keys
export OPENAI_API_KEY=your_api_key_here
export ANTHROPIC_PROJECT_ID=your_api_key_here

# run Clean Coder
python clean_coder_pipeline.py
```
or check detailed instructions [how to start in documentation](https://clean-coder.dev/quick_start/programmer_pipeline/).


## Key advantages:

- [Manager agent](https://clean-coder.dev/quick_start/manager/) that plans thoroughly-descripted tasks using Todoist and supervises whole project, same as human scrum master.
- [Programmer agents](https://clean-coder.dev/quick_start/programmer_pipeline/) that effectively executes manager planned tasks. They has well-designed context pipeline with only clean input context in it and with advanced techniques to make it more intelligent.
- Ability to create a [frontend based on images](https://clean-coder.dev/features/working_with_images/) with designs.
- You can [speak to Clean Coder](https://clean-coder.dev/features/talk_to_cc/) instead of writing to provide your feedback or assign task.
- Automatic file linting preventing agent to introduce wrong change and [log check for self-debug](https://clean-coder.dev/advanced_features_installation/logs_check/).
- File Researcher agent with (but not only) [RAG tool](https://clean-coder.dev/advanced_features_installation/similarity_search_for_researcher/) for effective searching code files.

## Demo videos

[![Demo video](https://img.youtube.com/vi/LLiABw4gY_w/maxresdefault.jpg)](https://youtu.be/LLiABw4gY_w "Demo video")

[![Demo video](https://img.youtube.com/vi/d5qbX-v4qwM/maxresdefault.jpg)](https://youtu.be/d5qbX-v4qwM "Demo video")

## Contibutions

All contributions to the project are very welcome!

If you're planning to make a major change, please open an issue first to discuss your proposed changes.
