import asyncio
from playwright.async_api import async_playwright

async def take_screenshot_1():
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await browser.new_page()
    await page.goto('http://localhost:5173/page1')
    await page.screenshot(path='E://Eksperiments/screenshot1.png')
    await browser.close()
    await p.stop()

async def take_screenshot_2():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await browser.new_page()
        await page.goto('http://localhost:5173/page2')
        await page.screenshot(path='E://Eksperiments/screenshot2.png')
        await browser.close()

async def take_screenshot_3():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto('http://localhost:5173/page3')
        await page.screenshot(path='E://Eksperiments/screenshot3.png')
        await browser.close()

async def main():
    # List of tasks
    tasks = [
        take_screenshot_1(),
        take_screenshot_2(),
        take_screenshot_3()
    ]
    # Execute the tasks concurrently
    await asyncio.gather(*tasks)


from playwright.async_api import async_playwright
import asyncio


async def make_screenshot():
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=False)
    page = await browser.new_page()

    # Login as intern
    await page.goto(f'http://localhost:5173/login')
    await page.fill('input[type="email"]', "frontend.feedback@intern")
    await page.fill('input[type="password"]', "123")
    await page.click('button[type="submit"]')
    await page.wait_for_load_state('networkidle', timeout=10000)

    # Navigate to profile edit page
    await page.goto(f'http://localhost:5173/profile/edit')
    await page.wait_for_selector('form')

    # Take full page screenshot
    await page.screenshot(path='E://Eksperiments/intern_profile_edit.png')

    await browser.close()
    await p.stop()


asyncio.run(make_screenshot())