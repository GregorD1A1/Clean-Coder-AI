from __future__ import annotations

from typing import Any, Dict, List

import requests

from todoist_api_python.endpoints import (
    COLLABORATORS_ENDPOINT,
    COMMENTS_ENDPOINT,
    COMPLETED_ITEMS_ENDPOINT,
    LABELS_ENDPOINT,
    PROJECTS_ENDPOINT,
    QUICK_ADD_ENDPOINT,
    SECTIONS_ENDPOINT,
    SHARED_LABELS_ENDPOINT,
    SHARED_LABELS_REMOVE_ENDPOINT,
    SHARED_LABELS_RENAME_ENDPOINT,
    TASKS_ENDPOINT,
    get_rest_url,
    get_sync_url,
)
from todoist_api_python.http_requests import delete, get, post
from todoist_api_python.models import (
    Collaborator,
    Comment,
    CompletedItems,
    Label,
    Project,
    QuickAddResult,
    Section,
    Task,
)


class TodoistAPI:
    def __init__(self, token: str, session: requests.Session | None = None) -> None:
        self._token: str = token
        self._session = session or requests.Session()

    def get_task(self, task_id: str) -> Task:
        endpoint = get_rest_url(f"{TASKS_ENDPOINT}/{task_id}")
        task = get(self._session, endpoint, self._token)
        return Task.from_dict(task)

    def get_tasks(self, **kwargs) -> List[Task]:
        ids = kwargs.pop("ids", None)

        if ids:
            kwargs.update({"ids": ",".join(str(i) for i in ids)})

        endpoint = get_rest_url(TASKS_ENDPOINT)
        tasks = get(self._session, endpoint, self._token, kwargs)
        return [Task.from_dict(obj) for obj in tasks]

    def add_task(self, content: str, **kwargs) -> Task:
        endpoint = get_rest_url(TASKS_ENDPOINT)
        data: Dict[str, Any] = {"content": content}
        data.update(kwargs)
        task = post(self._session, endpoint, self._token, data=data)
        return Task.from_dict(task)

    def update_task(self, task_id: str, **kwargs) -> bool:
        endpoint = get_rest_url(f"{TASKS_ENDPOINT}/{task_id}")
        return post(self._session, endpoint, self._token, data=kwargs)

    def close_task(self, task_id: str, **kwargs) -> bool:
        endpoint = get_rest_url(f"{TASKS_ENDPOINT}/{task_id}/close")
        return post(self._session, endpoint, self._token, data=kwargs)

    def reopen_task(self, task_id: str, **kwargs) -> bool:
        endpoint = get_rest_url(f"{TASKS_ENDPOINT}/{task_id}/reopen")
        return post(self._session, endpoint, self._token, data=kwargs)

    def delete_task(self, task_id: str, **kwargs) -> bool:
        endpoint = get_rest_url(f"{TASKS_ENDPOINT}/{task_id}")
        return delete(self._session, endpoint, self._token, args=kwargs)

    def quick_add_task(self, text: str) -> QuickAddResult:
        endpoint = get_sync_url(QUICK_ADD_ENDPOINT)
        data = {
            "text": text,
            "meta": True,
            "auto_reminder": True,
        }
        task_data = post(self._session, endpoint, self._token, data=data)
        return QuickAddResult.from_quick_add_response(task_data)

    def get_project(self, project_id: str) -> Project:
        endpoint = get_rest_url(f"{PROJECTS_ENDPOINT}/{project_id}")
        project = get(self._session, endpoint, self._token)
        return Project.from_dict(project)

    def get_projects(self) -> List[Project]:
        endpoint = get_rest_url(PROJECTS_ENDPOINT)
        projects = get(self._session, endpoint, self._token)
        return [Project.from_dict(obj) for obj in projects]

    def add_project(self, name: str, **kwargs) -> Project:
        endpoint = get_rest_url(PROJECTS_ENDPOINT)
        data: Dict[str, Any] = {"name": name}
        data.update(kwargs)
        project = post(self._session, endpoint, self._token, data=data)
        return Project.from_dict(project)

    def update_project(self, project_id: str, **kwargs) -> bool:
        endpoint = get_rest_url(f"{PROJECTS_ENDPOINT}/{project_id}")
        return post(self._session, endpoint, self._token, data=kwargs)

    def delete_project(self, project_id: str, **kwargs) -> bool:
        endpoint = get_rest_url(f"{PROJECTS_ENDPOINT}/{project_id}")
        return delete(self._session, endpoint, self._token, args=kwargs)

    def get_collaborators(self, project_id: str) -> List[Collaborator]:
        endpoint = get_rest_url(
            f"{PROJECTS_ENDPOINT}/{project_id}/{COLLABORATORS_ENDPOINT}"
        )
        collaborators = get(self._session, endpoint, self._token)
        return [Collaborator.from_dict(obj) for obj in collaborators]

    def get_section(self, section_id: str) -> Section:
        endpoint = get_rest_url(f"{SECTIONS_ENDPOINT}/{section_id}")
        section = get(self._session, endpoint, self._token)
        return Section.from_dict(section)

    def get_sections(self, **kwargs) -> List[Section]:
        endpoint = get_rest_url(SECTIONS_ENDPOINT)
        sections = get(self._session, endpoint, self._token, kwargs)
        return [Section.from_dict(obj) for obj in sections]

    def add_section(self, name: str, project_id: str, **kwargs) -> Section:
        endpoint = get_rest_url(SECTIONS_ENDPOINT)
        data = {"name": name, "project_id": project_id}
        data.update(kwargs)
        section = post(self._session, endpoint, self._token, data=data)
        return Section.from_dict(section)

    def update_section(self, section_id: str, name: str, **kwargs) -> bool:
        endpoint = get_rest_url(f"{SECTIONS_ENDPOINT}/{section_id}")
        data: Dict[str, Any] = {"name": name}
        data.update(kwargs)
        return post(self._session, endpoint, self._token, data=data)

    def delete_section(self, section_id: str, **kwargs) -> bool:
        endpoint = get_rest_url(f"{SECTIONS_ENDPOINT}/{section_id}")
        return delete(self._session, endpoint, self._token, args=kwargs)

    def get_comment(self, comment_id: str) -> Comment:
        endpoint = get_rest_url(f"{COMMENTS_ENDPOINT}/{comment_id}")
        comment = get(self._session, endpoint, self._token)
        return Comment.from_dict(comment)

    def get_comments(self, **kwargs) -> List[Comment]:
        endpoint = get_rest_url(COMMENTS_ENDPOINT)
        comments = get(self._session, endpoint, self._token, kwargs)
        return [Comment.from_dict(obj) for obj in comments]

    def add_comment(self, content: str, **kwargs) -> Comment:
        endpoint = get_rest_url(COMMENTS_ENDPOINT)
        data = {"content": content}
        data.update(kwargs)
        comment = post(self._session, endpoint, self._token, data=data)
        return Comment.from_dict(comment)

    def update_comment(self, comment_id: str, content: str, **kwargs) -> bool:
        endpoint = get_rest_url(f"{COMMENTS_ENDPOINT}/{comment_id}")
        data: Dict[str, Any] = {"content": content}
        data.update(kwargs)
        return post(self._session, endpoint, self._token, data=data)

    def delete_comment(self, comment_id: str, **kwargs) -> bool:
        endpoint = get_rest_url(f"{COMMENTS_ENDPOINT}/{comment_id}")
        return delete(self._session, endpoint, self._token, args=kwargs)

    def get_label(self, label_id: str) -> Label:
        endpoint = get_rest_url(f"{LABELS_ENDPOINT}/{label_id}")
        label = get(self._session, endpoint, self._token)
        return Label.from_dict(label)

    def get_labels(self) -> List[Label]:
        endpoint = get_rest_url(LABELS_ENDPOINT)
        labels = get(self._session, endpoint, self._token)
        return [Label.from_dict(obj) for obj in labels]

    def add_label(self, name: str, **kwargs) -> Label:
        endpoint = get_rest_url(LABELS_ENDPOINT)
        data = {"name": name}
        data.update(kwargs)
        label = post(self._session, endpoint, self._token, data=data)
        return Label.from_dict(label)

    def update_label(self, label_id: str, **kwargs) -> bool:
        endpoint = get_rest_url(f"{LABELS_ENDPOINT}/{label_id}")
        return post(self._session, endpoint, self._token, data=kwargs)

    def delete_label(self, label_id: str, **kwargs) -> bool:
        endpoint = get_rest_url(f"{LABELS_ENDPOINT}/{label_id}")
        return delete(self._session, endpoint, self._token, args=kwargs)

    def get_shared_labels(self) -> List[str]:
        endpoint = get_rest_url(SHARED_LABELS_ENDPOINT)
        return get(self._session, endpoint, self._token)

    def rename_shared_label(self, name: str, new_name: str) -> bool:
        endpoint = get_rest_url(SHARED_LABELS_RENAME_ENDPOINT)
        data = {"name": name, "new_name": new_name}
        return post(self._session, endpoint, self._token, data=data)

    def remove_shared_label(self, name: str) -> bool:
        endpoint = get_rest_url(SHARED_LABELS_REMOVE_ENDPOINT)
        data = {"name": name}
        return post(self._session, endpoint, self._token, data=data)

    def get_completed_items(
        self,
        project_id: str | None = None,
        section_id: str | None = None,
        item_id: str | None = None,
        last_seen_id: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> CompletedItems:
        endpoint = get_sync_url(COMPLETED_ITEMS_ENDPOINT)
        completed_items = get(
            self._session,
            endpoint,
            self._token,
            {
                "project_id": project_id,
                "section_id": section_id,
                "item_id": item_id,
                "last_seen_id": last_seen_id,
                "limit": limit,
                "cursor": cursor,
            },
        )
        return CompletedItems.from_dict(completed_items)
