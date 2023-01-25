import asyncio
import datetime
import re

from starlette.requests import Request
from starlette.responses import Response

from .firestore import client
from .utilities import get_dm_channel_id, get_users, say

standup_channel = "CANLZB1L3"  # "CBH18KG8G"


def get_collection_name():
    date_format = "%Y-%m-%d"
    now = datetime.datetime.utcnow()
    day_name = now.strftime("%A")
    weekend_offsets = {"Friday": 3, "Saturday": 2, "Sunday": 1}
    day_offset = weekend_offsets.get(day_name, 1)

    if day_name not in ["Saturday", "Sunday"]:
        if (now.hour < 14) or (now.hour == 14 and now.minute <= 31):
            return now.strftime(date_format)
        else:
            return (now + datetime.timedelta(days=day_offset)).strftime(date_format)
    else:
        return (now + datetime.timedelta(days=day_offset)).strftime(date_format)


def get_latest_updates():
    """
    Returns dictionary of users -> updates
    """
    date = get_collection_name()
    collection = client.collection(f"standup/{date}/users")
    updates = collection.get()
    user_dict = {doc.id: (doc.to_dict() or {}).get("updates") for doc in updates}
    return user_dict


def pop_user_updates(user):
    """
    Deletes a user's updates and returns the old update
    """
    date = get_collection_name()
    collection = client.collection(f"standup/{date}/users")
    user_doc = collection.document(user)
    old_update = (user_doc.get().to_dict() or {}).get("updates")
    user_doc.delete()
    return old_update


def update_user_updates(user, update):
    date = get_collection_name()
    collection = client.collection(f"standup/{date}/users")
    user_doc = collection.document(user)
    current_status = user_doc.get().to_dict()
    if current_status is None:
        user_doc.create({"updates": update})
    else:
        new_update = current_status.get("updates", "") + "\n" + update
        user_doc.update({"updates": new_update})


async def standup_handler(request: Request):
    payload = await request.form()
    user = payload.get("user_name")
    update = payload.get("text")
    clear_match = re.compile("^clear($|\\s)")
    if clear_match.match(update):
        old = pop_user_updates(user)
        if old is None:
            return Response("No updates to clear!")
        else:
            old = old.replace("\n", "")  # ensures strikethrough formats
            return Response(f"~{old}~")

    show_match = re.compile("^show($|\\s)")
    if show_match.match(update):
        current_updates = get_latest_updates()
        current_update = current_updates.get(
            user, f"I haven't received any updates from you yet, {user}."
        )
        return Response(current_update)

    update_user_updates(user, update)
    return Response(f"Thanks {user}!")
