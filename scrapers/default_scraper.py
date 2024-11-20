import requests

def execute_scrape(url, work_dir):
    response = requests.get(url)
    if response.status_code == 200:
        return response
    else:
        return response.status_code