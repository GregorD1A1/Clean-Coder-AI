from src.agents.executor_agent import Executor
import shutil


def cleanup_work_dir():
    shutil.rmtree("sandbox_work_dir")

executor = Executor(set(), "sandbox_work_dir")

task = "Create fastapi app with few endpoints."
plan = """1. Create main.py in flask looking like:
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the Flask application!"

@app.route('/hello/<name>')
def hello_name(name):
    return "Hello " + name

@app.route('/square/<int:number>')
def square(number):
    return jsonify(result=number**2)

if __name__ == '__main__':
    app.run(debug=True)
```
"""

executor.do_task(task, plan)
cleanup_work_dir()
