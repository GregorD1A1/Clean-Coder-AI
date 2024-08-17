from __future__ import annotations

from typing import List
from urllib.parse import urlencode

import requests
from requests import Session

from todoist_api_python.endpoints import (
    AUTHORIZE_ENDPOINT,
    REVOKE_TOKEN_ENDPOINT,
    TOKEN_ENDPOINT,
    get_auth_url,
    get_sync_url,
)
from todoist_api_python.http_requests import post
from todoist_api_python.models import AuthResult
from todoist_api_python.utils import run_async


def get_auth_token(
    client_id: str, client_secret: str, code: str, session: Session | None = None
) -> AuthResult:
    endpoint = get_auth_url(TOKEN_ENDPOINT)
    session = session or requests.Session()
    payload = {"client_id": client_id, "client_secret": client_secret, "code": code}
    response = post(session=session, url=endpoint, data=payload)

    return AuthResult.from_dict(response)


async def get_auth_token_async(
    client_id: str, client_secret: str, code: str
) -> AuthResult:
    return await run_async(lambda: get_auth_token(client_id, client_secret, code))


def revoke_auth_token(
    client_id: str, client_secret: str, token: str, session: Session | None = None
) -> bool:
    endpoint = get_sync_url(REVOKE_TOKEN_ENDPOINT)
    session = session or requests.Session()
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "access_token": token,
    }
    response = post(session=session, url=endpoint, data=payload)

    return response


async def revoke_auth_token_async(
    client_id: str, client_secret: str, token: str
) -> bool:
    return await run_async(lambda: revoke_auth_token(client_id, client_secret, token))


def get_authentication_url(client_id: str, scopes: List[str], state: str) -> str:
    if len(scopes) == 0:
        raise Exception("At least one authorization scope should be requested.")

    query = {"client_id": client_id, "scope": ",".join(scopes), "state": state}

    auth_url = get_auth_url(AUTHORIZE_ENDPOINT)

    return f"{auth_url}?{urlencode(query)}"
