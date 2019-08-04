import asyncio
import json
import os
import random
import re
from concurrent.futures import ThreadPoolExecutor

import schedule
from apistar.http import Body, Response
import google.cloud.firestore

from .github import create_issue
from .utilities import (
    get_dm_channel_id,
    say,
    public_speak,
    get_public_thread,
    get_user_info,
)
from .karma import update_karma

executor = ThreadPoolExecutor(max_workers=3)
USERS = {}

GIT_SHA = os.environ.get("GIT_SHA")
MARVIN_ID = "UBEEMJZFX"
quotes = [
    '"Let’s build robots with Genuine People Personalities," they said. So they tried it out with me. I’m a personality prototype. You can tell, can’t you?',
    "It’s the people you meet in this job that really get you down.",
    "This is the sort of thing you lifeforms enjoy, is it?",
    "Don’t pretend you want to talk to me, I know you hate me.",
    "I think you ought to know I’m feeling very depressed.",
    "I would like to say that it is a very great pleasure, honour and privilege for me to talk to you, but I can’t because my lying circuits are all out of commission.",
    "Incredible. It’s even worse than I thought it would be.",
    "This will all end in tears, I just know it.",
    "Here I am, brain the size of a planet, and they ask me to talk to you. Call that job satisfaction? ’Cos I don’t.",
    "It gives me a headache just trying to think down to your level.",
    "I’d give you advice, but you wouldn’t listen. No one ever does.",
    ":marvin:",
    ":marvin-parrot:",
    "Do you want me to sit in a corner and rust, or just fall apart where I'm standing?",
    "Don't feel you have to take any notice of me, please.",
    "Why should I want to make anything up? Life’s bad enough as it is without wanting to invent any more of it.",
]

firestore = None

karma_regex = re.compile("^(.+[^\s])(\+{2}|\-{2})(\s*|$)$")


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
    global firestore
    if firestore is None:
        firestore = google.cloud.firestore.Client(project="prefect-marvin")

    new_users = {
        user.id: user.to_dict() for user in firestore.collection("users").get()
    }
    # add new users to USERS
    USERS.update(new_users)
    # delete old users from USERS -- don't clear() because we don't want USERS empty
    for uid in list(USERS.keys()):
        if uid not in new_users:
            del USERS[uid]


async def event_handler(data: Body):
    # for validating your URL with slack
    json_data = json.loads(data)
    is_challenge = json_data.get("type") == "url_verification"
    if is_challenge:
        return json_data["challenge"]

    event = json_data.get("event", {})
    event_type = event.get("type")
    if event_type == "app_mention" or MARVIN_ID in event.get("text", ""):
        return app_mention(event)
    elif event_type == "emoji_changed" and event.get("subtype") == "add":
        return emoji_added(event)
    elif event_type == "message" and event.get("bot_id") == "BBGMPFDHQ":
        return github_mention(event)
    elif event_type == "message" and event.get("bot_id") == "BDUBG9WAD":
        return notion_mention(event)
    elif event_type == "message" and event.get("bot_id") is None:
        positive_match = karma_regex.match(event.get("text", ""))
        if positive_match:
            return karma_handler(positive_match, event)


def app_mention(event):
    who_spoke = event.get("user", "")
    if who_spoke != MARVIN_ID:
        quote = random.choice(quotes)
        say(quote, channel=event.get("channel"), thread_ts=event.get("thread_ts"))
    return Response("")


def emoji_added(event):
    name = event.get("name", "grey_question")
    psa = f"*PSA*: A new slackmoji :{name}: was added! :more_you_know:"
    psa_channel = "CANPVTSKU"  # random
    say(psa, channel=psa_channel)
    return Response("")


def github_mention(event):
    data = event.get("attachments", [{}])[0]
    text = data.get("text", "")

    was_mentioned = {u["slack"]: (f"@{u['github']}" in text) for u in USERS.values()}
    for slack_id, mentioned in was_mentioned.items():
        if not mentioned:
            continue
        else:
            link = data.get("title_link", "link unavailable")
            msg = f"You were mentioned on GitHub @ {link}"
            say(msg, channel=get_dm_channel_id(slack_id))


def notion_mention(event):
    text = "\n".join(d.get("text", "") for d in event.get("attachments", [{}]))

    was_mentioned = {u["slack"]: (f"@{u['notion']}" in text) for u in USERS.values()}
    for slack_id, mentioned in was_mentioned.items():
        if not mentioned:
            continue
        else:
            link_pattern = re.compile("\*<(.*)\|.*\*")
            link = link_pattern.findall(event.get("text", ""))
            if link:
                formatted_link = link[0].lstrip("\"'").rstrip("\"'")  # remove quotes
                msg = f"You were mentioned on Notion @ {formatted_link}"
            else:
                msg = f"You were mentioned on Notion, but I don't have the link available..."
            say(msg, channel=get_dm_channel_id(slack_id))


async def version_handler():
    base_url = "https://github.com/PrefectHQ/marvin/commit/"
    return f"{base_url}{GIT_SHA}"


def karma_handler(regex_match, event):
    response_text = update_karma(regex_match)
    say(response_text, channel=event.get("channel"))
    return Response("")


async def public_event_handler(data: Body):
    # for validating your URL with slack
    json_data = json.loads(data)
    is_challenge = json_data.get("type") == "url_verification"
    if is_challenge:
        return json_data["challenge"]

    event = json_data.get("event", {})
    event_type = event.get("type")
    if event_type != "app_mention":
        return Response("")

    # only chris and jeremiah allowed to use this
    who_spoke = event.get("user", "")
    if who_spoke != "UKNSNMUE6":
        return Response("")

    patt = re.compile('archive\s"(.*?)"')
    matches = patt.findall(event.get("text", "").replace("“", '"').replace("”", '"'))
    if matches:
        issue_body = ""
        thread = get_public_thread(channel=event["channel"], ts=event["thread_ts"])
        for msg in thread:
            issue_body += "**{}**: ".format(get_user_info(user=msg["user"]))
            issue_body += msg["text"] + "\n\n"

        out = create_issue(
            title=matches[0], body=issue_body, labels=["slack"], issue_state="closed"
        )
        public_speak(
            text=out["html_url"], channel=event["channel"], thread_ts=event["thread_ts"]
        )
