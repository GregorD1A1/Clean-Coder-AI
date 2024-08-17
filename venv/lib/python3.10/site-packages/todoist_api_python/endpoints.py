from urllib.parse import urljoin

BASE_URL = "https://api.todoist.com"
AUTH_BASE_URL = "https://todoist.com"
SYNC_VERSION = "v9"
REST_VERSION = "v2"

SYNC_API = urljoin(BASE_URL, f"/sync/{SYNC_VERSION}/")
REST_API = urljoin(BASE_URL, f"/rest/{REST_VERSION}/")


TASKS_ENDPOINT = "tasks"
PROJECTS_ENDPOINT = "projects"
COLLABORATORS_ENDPOINT = "collaborators"
SECTIONS_ENDPOINT = "sections"
COMMENTS_ENDPOINT = "comments"
LABELS_ENDPOINT = "labels"
SHARED_LABELS_ENDPOINT = "labels/shared"
SHARED_LABELS_RENAME_ENDPOINT = f"{SHARED_LABELS_ENDPOINT}/rename"
SHARED_LABELS_REMOVE_ENDPOINT = f"{SHARED_LABELS_ENDPOINT}/remove"
QUICK_ADD_ENDPOINT = "quick/add"

AUTHORIZE_ENDPOINT = "oauth/authorize"
TOKEN_ENDPOINT = "oauth/access_token"
REVOKE_TOKEN_ENDPOINT = "access_tokens/revoke"

COMPLETED_ITEMS_ENDPOINT = "archive/items"


def get_rest_url(relative_path: str) -> str:
    return urljoin(REST_API, relative_path)


def get_sync_url(relative_path: str) -> str:
    return urljoin(SYNC_API, relative_path)


def get_auth_url(relative_path: str) -> str:
    return urljoin(AUTH_BASE_URL, relative_path)
