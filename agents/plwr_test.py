from playwright.sync_api import sync_playwright
p = sync_playwright().start()

from playwright._impl._errors import TimeoutError


browser = p.chromium.launch(headless=False)
page = browser.new_page()
try:
    # Login as campaign user
    page.goto('http://localhost:5173/login')
    page.fill('input[type="email"]', 'frontend.feedback@campaign')
    page.fill('input[type="password"]', '123')
    page.click('button[type="submit"]')
    page.wait_for_url('**/')
    page.wait_for_load_state('networkidle')

    # Navigate to campaign profile page
    # Note: Using a known UUID for the test campaign profile
    page.goto('http://localhost:5173/campaign/test-campaign-uuid')

    # Wait for the profile content to load
    page.wait_for_selector('.campaign-profile')
    page.wait_for_selector('.campaign-details')

    # Ensure all dynamic content is loaded
    page.wait_for_load_state('networkidle')
    output = page.screenshot()
except Exception as e:
    output = f"{type(e).__name__}: {e}"
browser.close()