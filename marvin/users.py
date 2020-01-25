import asyncio
import json
import os
import random
import re
from concurrent.futures import ThreadPoolExecutor

import schedule
from starlette.requests import Request
from starlette.responses import Response

from .firestore import client
from .github import create_issue
from .karma import update_karma
from .utilities import (
    get_dm_channel_id,
    get_public_thread,
    get_user_info,
    public_speak,
    say,
)

__all__ = ["USERS", "create_user"]

executor = ThreadPoolExecutor(max_workers=3)
USERS = {}


def create_user(
    email, name, slack, office="DC", standup=False, github=None, notion=None
):
    """
    Convenience function for adding Prefect users to firestore
    """
    client.collection("users").add(
        dict(
            email=email,
            name=name,
            slack=slack,
            office=office,
            standup=standup,
            github=github,
            notion=notion,
        )
    )


def get_all_users():
    """
    Returns all users in the database
    """
    return list(USERS.values())


async def schedule_refresh_users():
    # run once for initial load
    await refresh_users()
    # schedule updates every hour
    schedule.every().hour.do(refresh_users)


async def refresh_users():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _refresh_users)


def _refresh_users():
    """
    Firestore doesn't have an async API so this should be run in a ThreadPool via the
    `refresh_users()` coroutine
    """
    import google.cloud.firestore

    global client
    if client is None:
        client = google.cloud.firestore.Client(project="prefect-marvin")

    new_users = {user.id: user.to_dict() for user in client.collection("users").get()}
    # add new users to USERS
    USERS.update(new_users)
    # delete old users from USERS -- don't clear() because we don't want USERS empty
    for uid in list(USERS.keys()):
        if uid not in new_users:
            del USERS[uid]