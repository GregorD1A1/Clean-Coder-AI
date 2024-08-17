from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, List, Literal

from todoist_api_python.utils import get_url_for_task

VIEW_STYLE = Literal["list", "board"]


@dataclass
class Project:
    color: str
    comment_count: int
    id: str
    is_favorite: bool
    is_inbox_project: bool
    is_shared: bool
    is_team_inbox: bool
    can_assign_tasks: bool
    name: str
    order: int
    parent_id: str | None
    url: str
    view_style: VIEW_STYLE

    @classmethod
    def from_dict(cls, obj):
        return cls(
            color=obj["color"],
            comment_count=obj["comment_count"],
            id=obj["id"],
            is_favorite=obj["is_favorite"],
            is_inbox_project=obj.get("is_inbox_project"),
            is_shared=obj["is_shared"],
            is_team_inbox=obj.get("is_team_inbox"),
            can_assign_tasks=obj.get("can_assign_tasks"),
            name=obj["name"],
            order=obj.get("order"),
            parent_id=obj.get("parent_id"),
            url=obj["url"],
            view_style=obj["view_style"],
        )


@dataclass
class Section:
    id: str
    name: str
    order: int
    project_id: str

    @classmethod
    def from_dict(cls, obj):
        return cls(
            id=obj["id"],
            name=obj["name"],
            order=obj["order"],
            project_id=obj["project_id"],
        )


@dataclass
class Due:
    date: str
    is_recurring: bool
    string: str

    datetime: str | None = None
    timezone: str | None = None

    @classmethod
    def from_dict(cls, obj):
        return cls(
            date=obj["date"],
            is_recurring=obj["is_recurring"],
            string=obj["string"],
            datetime=obj.get("datetime"),
            timezone=obj.get("timezone"),
        )

    def to_dict(self):
        return {
            "date": self.date,
            "is_recurring": self.is_recurring,
            "string": self.string,
            "datetime": self.datetime,
            "timezone": self.timezone,
        }

    @classmethod
    def from_quick_add_response(cls, obj):
        due = obj.get("due")

        if not due:
            return None

        timezone = due.get("timezone")

        datetime: str | None = None

        if timezone:
            datetime = due["date"]

        return cls(
            date=due["date"],
            is_recurring=due["is_recurring"],
            string=due["string"],
            datetime=datetime,
            timezone=timezone,
        )


@dataclass
class Task:
    assignee_id: str | None
    assigner_id: str | None
    comment_count: int
    is_completed: bool
    content: str
    created_at: str
    creator_id: str
    description: str
    due: Due | None
    id: str
    labels: List[str]
    order: int
    parent_id: str | None
    priority: int
    project_id: str
    section_id: str | None
    url: str
    duration: Duration | None

    sync_id: str | None = None

    @classmethod
    def from_dict(cls, obj):
        due: Due | None = None
        duration: Duration | None = None

        if obj.get("due"):
            due = Due.from_dict(obj["due"])

        if obj.get("duration"):
            duration = Duration.from_dict(obj["duration"])

        return cls(
            assignee_id=obj.get("assignee_id"),
            assigner_id=obj.get("assigner_id"),
            comment_count=obj["comment_count"],
            is_completed=obj["is_completed"],
            content=obj["content"],
            created_at=obj["created_at"],
            creator_id=obj["creator_id"],
            description=obj["description"],
            due=due,
            id=obj["id"],
            labels=obj.get("labels"),
            order=obj.get("order"),
            parent_id=obj.get("parent_id"),
            priority=obj["priority"],
            project_id=obj["project_id"],
            section_id=obj["section_id"],
            url=obj["url"],
            duration=duration
        )

    def to_dict(self):
        due: dict | None = None

        if self.due:
            due = self.due.to_dict()

        return {
            "assignee_id": self.assignee_id,
            "assigner_id": self.assigner_id,
            "comment_count": self.comment_count,
            "is_completed": self.is_completed,
            "content": self.content,
            "created_at": self.created_at,
            "creator_id": self.creator_id,
            "description": self.description,
            "due": due,
            "id": self.id,
            "labels": self.labels,
            "order": self.order,
            "parent_id": self.parent_id,
            "priority": self.priority,
            "project_id": self.project_id,
            "section_id": self.section_id,
            "sync_id": self.sync_id,
            "url": self.url,
            "duration": self.duration
        }

    @classmethod
    def from_quick_add_response(cls, obj):
        due: Due | None = None
        duration: Duration | None = None

        if obj.get("due"):
            due = Due.from_quick_add_response(obj)

        if obj.get("duration"):
            duration = Duration.from_dict(obj["duration"])

        return cls(
            assignee_id=obj.get("responsible_uid"),
            assigner_id=obj.get("assigned_by_uid"),
            comment_count=0,
            is_completed=False,
            content=obj["content"],
            created_at=obj["added_at"],
            creator_id=obj["added_by_uid"],
            description=obj["description"],
            due=due,
            duration=duration,
            id=obj["id"],
            labels=obj["labels"],
            order=obj["child_order"],
            parent_id=obj["parent_id"] or None,
            priority=obj["priority"],
            project_id=obj["project_id"],
            section_id=obj["section_id"] or None,
            sync_id=obj["sync_id"],
            url=get_url_for_task(obj["id"], obj["sync_id"]),
        )


@dataclass
class QuickAddResult:
    task: Task

    resolved_project_name: str | None = None
    resolved_assignee_name: str | None = None
    resolved_label_names: List[str] | None = None
    resolved_section_name: str | None = None

    @classmethod
    def from_quick_add_response(cls, obj):
        project_data = obj["meta"].get("project", {})
        assignee_data = obj["meta"].get("assignee", {})
        section_data = obj["meta"].get("section", {})

        resolved_project_name = None
        resolved_assignee_name = None
        resolved_section_name = None

        if project_data and len(project_data) == 2:
            resolved_project_name = obj["meta"]["project"][1]

        if assignee_data and len(assignee_data) == 2:
            resolved_assignee_name = obj["meta"]["assignee"][1]

        if section_data and len(section_data) == 2:
            resolved_section_name = obj["meta"]["section"][1]

        return cls(
            task=Task.from_quick_add_response(obj),
            resolved_project_name=resolved_project_name,
            resolved_assignee_name=resolved_assignee_name,
            resolved_label_names=list(obj["meta"]["labels"].values()),
            resolved_section_name=resolved_section_name,
        )


@dataclass
class Collaborator:
    id: str
    email: str
    name: str

    @classmethod
    def from_dict(cls, obj):
        return cls(
            id=obj["id"],
            email=obj["email"],
            name=obj["name"],
        )


@dataclass
class Attachment:
    resource_type: str | None = None

    file_name: str | None = None
    file_size: int | None = None
    file_type: str | None = None
    file_url: str | None = None
    file_duration: int | None = None
    upload_state: str | None = None

    image: str | None = None
    image_width: int | None = None
    image_height: int | None = None

    url: str | None = None
    title: str | None = None

    @classmethod
    def from_dict(cls, obj):
        return cls(
            resource_type=obj.get("resource_type"),
            file_name=obj.get("file_name"),
            file_size=obj.get("file_size"),
            file_type=obj.get("file_type"),
            file_url=obj.get("file_url"),
            upload_state=obj.get("upload_state"),
            image=obj.get("image"),
            image_width=obj.get("image_width"),
            image_height=obj.get("image_height"),
            url=obj.get("url"),
            title=obj.get("title"),
        )


@dataclass
class Comment:
    attachment: Attachment | None
    content: str
    id: str
    posted_at: str
    project_id: str | None
    task_id: str | None

    @classmethod
    def from_dict(cls, obj):
        attachment: Attachment | None = None

        if "attachment" in obj and obj["attachment"] is not None:
            attachment = Attachment.from_dict(obj["attachment"])

        return cls(
            attachment=attachment,
            content=obj["content"],
            id=obj["id"],
            posted_at=obj["posted_at"],
            project_id=obj.get("project_id"),
            task_id=obj.get("task_id"),
        )


@dataclass
class Label:
    id: str
    name: str
    color: str
    order: int
    is_favorite: bool

    @classmethod
    def from_dict(cls, obj):
        return cls(
            id=obj["id"],
            name=obj["name"],
            color=obj["color"],
            order=obj["order"],
            is_favorite=obj["is_favorite"],
        )


@dataclass
class AuthResult:
    access_token: str
    state: str

    @classmethod
    def from_dict(cls, obj):
        return cls(
            access_token=obj["access_token"],
            state=obj["state"],
        )


@dataclass
class Item:
    id: str
    user_id: str
    project_id: str
    content: str
    description: str
    priority: int
    child_order: int
    collapsed: bool
    labels: list[str]
    checked: bool
    is_deleted: bool
    added_at: str
    due: Due | None = None
    parent_id: int | None = None
    section_id: str | None = None
    day_order: int | None = None
    added_by_uid: str | None = None
    assigned_by_uid: str | None = None
    responsible_uid: str | None = None
    sync_id: str | None = None
    completed_at: str | None = None

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> Item:
        params = {f.name: obj[f.name] for f in fields(cls) if f.name in obj}
        if (due := obj.get("due")) is not None:
            params["due"] = Due.from_dict(due)

        return cls(**params)


@dataclass
class ItemCompletedInfo:
    item_id: str
    completed_items: int

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> ItemCompletedInfo:
        return cls(**{f.name: obj[f.name] for f in fields(cls)})


@dataclass
class CompletedItems:
    items: list[Item]
    total: int
    completed_info: list[ItemCompletedInfo]
    has_more: bool
    next_cursor: str | None = None

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> CompletedItems:
        return cls(
            items=[Item.from_dict(v) for v in obj["items"]],
            total=obj["total"],
            completed_info=[
                ItemCompletedInfo.from_dict(v) for v in obj["completed_info"]
            ],
            has_more=obj["has_more"],
            next_cursor=obj.get("next_cursor"),
        )


@dataclass
class Duration(object):
    amount: int
    unit: str

    @classmethod
    def from_dict(cls, obj):
        return cls(
            amount=obj["amount"],
            unit=obj["unit"],
        )

    def to_dict(self):
        return {
            "amount": self.amount,
            "unit": self.unit,
        }
