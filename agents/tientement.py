from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # Launch browser
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto('http://localhost:5173/')

    # Wait for the redirection to complete and page to stabilize
    page.wait_for_url('**/register')
    page.wait_for_load_state('networkidle')

    # Take a screenshot of the registration page we were redirected to
    page.screenshot(path='E://Eksperiments/redirect_to_register.png')

    # Close the browser
    browser.close()