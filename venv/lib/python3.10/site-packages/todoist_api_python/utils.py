from __future__ import annotations

import asyncio

SHOW_TASK_ENDPOINT = "https://todoist.com/showTask"


def get_url_for_task(task_id: int, sync_id: int | None) -> str:
    return (
        f"{SHOW_TASK_ENDPOINT}?id={task_id}&sync_id={sync_id}"
        if sync_id
        else f"{SHOW_TASK_ENDPOINT}?id={task_id}"
    )


async def run_async(func):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func)
