import asyncio
import datetime
import re
import schedule
from apistar.http import RequestData

from .utilities import get_dm_channel_id, get_users, say


standup_channel = "CBH18KG8G"
UPDATES = {}


async def scheduler():
    schedule.every().day.at("13:30").do(_pre_standup)
    schedule.every().day.at("14:00").do(_post_standup)
    while True:
        await asyncio.sleep(5)
        schedule.run_pending()


async def standup_handler(data: RequestData):
    payload = data.to_dict() if not isinstance(data, dict) else data
    user = payload.get("user_name")
    update = payload.get("text")
    clear_match = re.compile("^clear($|\s)")
    if clear_match.match(update):
        old = UPDATES.pop(user, None)
        if old is None:
            return "No updates to clear!"
        else:
            old = old.replace("\n", "")  # ensures strikethrough formats
            return f"~{old}~"

    show_match = re.compile("^show($|\s)")
    if show_match.match(update):
        current_update = UPDATES.get(
            user, f"I haven't received any updates from you yet, {user}."
        )
        return current_update

    if user in UPDATES:
        UPDATES[user] += update + "\n"
    else:
        UPDATES[user] = update + "\n"
    return f"Thanks {user}!"


def _pre_standup():
    if not _is_weekday():
        return
    users = get_users()
    for name, uid in users.items():
        if UPDATES.get(name) is None:
            say(
                f"Hi {name}! I haven't heard from you yet; what updates do you have for the team today? Please respond by using the slash command `/standup`,  and remember: your response will be shared!",
                channel=get_dm_channel_id(uid),
                mrkdwn="true",
            )
            UPDATES[name] = ""


def _post_standup():
    if not _is_weekday():
        return
    public_msg = "<!here> are today's standup updates:\n" + "=" * 30
    for user, update in UPDATES.items():
        public_msg += f"\n*{user}*: {update}"
    say(public_msg, channel=standup_channel)
    UPDATES.clear()


def _is_weekday():
    now = datetime.datetime.now()
    day = now.strftime("%A")
    if day in ["Saturday", "Sunday"]:
        return False
    else:
        return True
