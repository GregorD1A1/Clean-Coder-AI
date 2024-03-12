from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import base64
import playwright

load_dotenv(find_dotenv())
client = OpenAI()


def visual_describe(img, prompt):
    with open(img, "rb") as image_file:
        img_encoded = base64.b64encode(image_file.read()).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                  {"type": "text", "text": prompt},
                  {
                    "type": "image_url",
                    "image_url": {
                      "url": f"data:image/jpeg;base64,{img_encoded}",
                    },
                  },
                ],
            }
        ],
        max_tokens=600,
    )

    return response.choices[0].message.content


def make_screenshot(endpoint, login_needed, commands):
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    if login_needed:
        page.goto('http://localhost:5555/login')
        page.fill('#username', 'juraj.kovac@op.pl')
        page.fill('#password', 'DnEcZTYB')
        page.click('.login-form button[type="submit"]')
    page.goto(f'http://localhost:5555/{endpoint}')

    for command in commands:
        action = command.get('action')
        selector = command.get('selector')
        value = command.get('value')
        if action == 'fill':
            page.fill(selector, value)
        elif action == 'click':
            page.click(selector)
        elif action == 'hover':
            page.hover(selector)

    page.screenshot(path='/home/autogen/autogen/takzyli-frontend/screenshots/screenshot.png')
    browser.close()
