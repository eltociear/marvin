import asyncio
import datetime
import google.cloud.firestore
import re
import schedule
from apistar.http import RequestData

from .utilities import get_dm_channel_id, get_users, say


client = google.cloud.firestore.Client(project="prefect-marvin")
standup_channel = "CANLZB1L3"  # "CBH18KG8G"


# schedule standup
async def schedule_standup():
    schedule.every().day.at("13:30").do(_pre_standup)
    schedule.every().day.at("14:00").do(_post_standup)


def get_collection_name():
    date_format = "%Y-%m-%d"
    now = datetime.datetime.utcnow()
    day_name = now.strftime("%A")
    weekend_offsets = {"Friday": 3, "Saturday": 2, "Sunday": 1}
    if now.hour < 14 and day_name not in ["Saturday", "Sunday"]:
        return now.strftime(date_format)
    elif now.hour >= 14 and day_name not in weekend_offsets:
        return (now + datetime.timedelta(days=1)).strftime(date_format)
    elif day_name in weekend_offsets:
        day_offset = weekend_offsets[day_name]
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


async def standup_handler(data: RequestData):
    payload = data.to_dict() if not isinstance(data, dict) else data
    user = payload.get("user_name")
    update = payload.get("text")
    clear_match = re.compile("^clear($|\s)")
    if clear_match.match(update):
        old = pop_user_updates(user)
        if old is None:
            return "No updates to clear!"
        else:
            old = old.replace("\n", "")  # ensures strikethrough formats
            return f"~{old}~"

    show_match = re.compile("^show($|\s)")
    if show_match.match(update):
        current_updates = get_latest_updates()
        current_update = current_updates.get(
            user, f"I haven't received any updates from you yet, {user}."
        )
        return current_update

    update_user_updates(user, update)
    return f"Thanks {user}!"


def _pre_standup():
    if not _is_weekday():
        return
    users = get_users()
    current_updates = get_latest_updates()
    for name, uid in users.items():
        if current_updates.get(name) is None:
            say(
                f"Hi {name}! I haven't heard from you yet; what updates do you have for the team today? Please respond by using the slash command `/standup`,  and remember: your response will be shared!",
                channel=get_dm_channel_id(uid),
                mrkdwn="true",
            )


def _post_standup():
    if not _is_weekday():
        return
    public_msg = "<!here> are today's standup updates:\n" + "=" * 30
    current_updates = get_latest_updates()
    for user, update in current_updates.items():
        public_msg += f"\n*{user}*: {update}"
    say(public_msg, channel=standup_channel)


def _is_weekday():
    now = datetime.datetime.now()
    day = now.strftime("%A")
    if day in ["Saturday", "Sunday"]:
        return False
    else:
        return True
