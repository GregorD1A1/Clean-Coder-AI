from playwright.sync_api import sync_playwright
p = sync_playwright().start()

from playwright._impl._errors import TimeoutError


browser = p.chromium.launch(headless=False)
page = browser.new_page()
try:
# Login as intern to view campaign profile
      page.goto('http://localhost:5173/login')
      page.fill('input[type="email"]', 'frontend.feedback@intern')
      page.fill('input[type="password"]', '123')
      page.click('button[type="submit"]')
      page.wait_for_url('**/')
      page.wait_for_load_state('networkidle')

      # Navigate to specific campaign profile
      page.goto('http://localhost:5173/campaigns/d4b9d557-94d3-463d-a7ac-28bb51ab7dc7')
      page.wait_for_load_state('networkidle')
      output = page.screenshot()
except TimeoutError as e:
      output = f"{type(e).__name__}: {e}"
browser.close()

print(output)