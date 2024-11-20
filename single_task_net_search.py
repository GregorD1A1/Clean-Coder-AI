import os
from utilities.user_input import user_input
from agents.doc_scraper_agent import harvest_website, single_clean_coder_pipeline, pull_documentation_from_internet

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


def run_scraper_pipeline(parse_task, work_dir, url):
    """Up-to-date documentation on selenium is loaded. Scrape job is executed."""
    # TODO: IMPlement
    # pull up-to-date documentation on selenium
    documentation = pull_documentation_from_internet(work_dir=work_dir, url="https://www.selenium.dev/selenium/docs/api/py/api.html")

    # prepare a scraping script using Selenium latest documentation.
    scrape_task = "Task instructing to prepare a scraper."
    file_path = single_clean_coder_pipeline(task=scrape_task, work_dir=work_dir, url=url,context=documentation)
    harvest_website(file_path)
    
    # prepare data parsing code (output csv)
    parsed_file_path = single_clean_coder_pipeline(task=parse_task, work_dir=work_dir, url=None)



if __name__ == "__main__":
    parse_task = user_input("Provide webpage parsing task to be executed.")
    work_dir = os.getenv("WORK_DIR")
    assert isinstance(work_dir, str)
    url = "www.sampleurl.com"
    parsed_file_path = run_scraper_pipeline(parse_task, work_dir, url)
