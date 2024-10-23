import os, sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
import shutil
from agents.executor_agent import Executor
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

def setup_work_dir():
    os.makedirs("sandbox_work_dir")
    shutil.copy2("projects_files/main_scenario_1.py", "sandbox_work_dir/main.py")

def cleanup_work_dir():
    shutil.rmtree("sandbox_work_dir")

setup_work_dir()
executor = Executor({"main.py"}, "sandbox_work_dir")

task = "Create fastapi app with few endpoints."
plan = """1. Create registration_logic.py file:

```python
from db import db
from auth import hash_password


def register_user(email: str, password: str):
    users_collection = db['users']
    
    if users_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(password)
    user_data = {
        "email": email,
        "password": hashed_password,
    }
    interns_collection.insert_one(user_data)
    send_registration_email(email)
    return {"message": "Intern registered successfully"}
```

2. Next, we need to create endpoint in main.py for handling registration:

first, add import statement on the beginning:
```python
+ from registration_logic import register_user
```

now, create endpoint:
```python
@app.post('/register')
async def register_endpoint():
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    return register_user(email, password)
```

That's it!

"""

executor.do_task(task, plan)
cleanup_work_dir()
