# Clean Coder framework
### Your AI junior programmer

Clean Coder is an AI code writer developed with special attention to providing a clean context to Large Language Models (LLMs). This enhances the quality of LLM responses and reduces costs.

Work of a programmer is often about making minor improvements to existing applications and expanding their capabilities, rather than building a whole new app from scratch. Unlike other AI coding frameworks, Clean Coder specializes in implementing changes within existing application.

## Key advantages:

- Well-designed context pipeline: The LLM only receives necessary information into its context. This significantly improves the LLM's attention and reduces costs.
- Ability to create a frontend based on images with designs.
- Automatic context updates after file modifications: There's no need to manually reload the file into the LLM context after adding a few lines.
- Automatic code linting and log check to ensure corectness of inserted code.
- Well-designed tools: These are specially designed to exchange appropriate parts of the code and navigate the file system. A human approval feature is added as a safety measure in case of code interference tools.

# How to work with Clean Coder

## Setup

Change name of `.env.template` file to `.env` and open it with text editor. Provide your OpenAI api key and path to project directory you will be working on.

It's very recommended to set up your project to write logs to file - that way executor agent will be able to check logs after changes are introduced and improve possible bugs. Provide full path to your log file after `LOG_FILE=` in .env to activate that feature.

Install required dependencies by running:

`pip install -r requirements.txt`

## Working process

Check out the demonstration video:

[![Demo video](https://img.youtube.com/vi/d5qbX-v4qwM/maxresdefault.jpg)](https://youtu.be/d5qbX-v4qwM "Demo video")

### 1. Define Task

In `clean_coder_pipeline.py`, modify the task variable. Describe your task in detail. It is advisable to provide "unit" tasks - smaller ones and run the program multiple times rather than asking it to perform a complex task all at once. Specify which files to edit and, if creating a frontend, which design templates to use.

### 2. Launch

Launch Clean Coder by running:

`python clean_coder_pipeline.py`

### 3. Researcher Agent

Launch the app. The first agent to begin work is the Researcher - its job is to examine files in the project directory and identify only the necessary files to work on. Additionally, it can locate image graphics as templates for frontend coding (you need to store designs somewhere in the project dir.).

Once the research is complete, the Researcher will display the suggested files to work on. Type 'ok' and press enter if you agree with his research or provide your feedback if you want it to add/remove some files.

### 4. Planner Agent

The Planner is the most responsible agent - it drafts the plan for code modifications. It's recommended to thoroughly review the plan it proposes and request it to make changes until the plan it outputs is satisfactory. Then, type 'ok' to proceed to the executor. Only the last planner message is provided to the executor, so ensure that it provides the complete plan in it.

### 5. Executor Agent

This is where the actual magic happens. The Executor will implement the planned changes to your project files. It will call tools in sequence, which will either modify files or create new ones. For tools that interact with the project, a safety mechanism is introduced - you need to confirm the tool execution by writing 'ok'. It's recommended to first check what change it intends to make and provide feedback if you think it might break something. After all changes are implemented, it will check the log file (if you set it up) and make further changes if there are issues with the logs. Next, it will ask you to confirm if everything is done as intended - provide feedback if you want it to improve something or type 'ok' to end the pipeline.