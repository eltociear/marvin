import asyncio
import json
import os
import random
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import schedule
from starlette.requests import Request
from starlette.responses import Response

from .users import USERS
from .github import create_issue
from .karma import update_karma
from .utilities import (
    get_dm_channel_id,
    promotional_signup,
    get_public_thread,
    get_public_message_permalink,
    get_user_info,
    public_speak,
    say,
)

executor = ThreadPoolExecutor(max_workers=3)

SURVEY_SAYS_RESPONSES = defaultdict(dict)
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


karma_regex = re.compile("^(.+[^\s])(\+{2}|\-{2})(\s*|$)$")


async def event_handler(request: Request):
    # for validating your URL with slack
    response = None

    # not sure if events are json or form-encoded
    try:
        json_data = await request.json()
    except:
        json_data = await request.form()

    is_challenge = json_data.get("type") == "url_verification"

    if is_challenge:
        return Response(json_data["challenge"])

    event = json_data.get("event", {})
    event_type = event.get("type")
    if event_type == "app_mention" or MARVIN_ID in event.get("text", ""):
        response = app_mention(event)
    elif event_type == "emoji_changed" and event.get("subtype") == "add":
        response = emoji_added(event)
    elif event_type == "message" and event.get("bot_id") == "BBGMPFDHQ":
        response = github_mention(event)
    elif event_type == "message" and event.get("bot_id") is None:
        positive_match = karma_regex.match(event.get("text", ""))
        if positive_match:
            response = karma_handler(positive_match, event)

    return Response(response)


def app_mention(event):
    who_spoke = event.get("user", "")
    if who_spoke != MARVIN_ID:
        quote = random.choice(quotes)
        say(quote, channel=event.get("channel"), thread_ts=event.get("thread_ts"))


def emoji_added(event):
    name = event.get("name", "grey_question")
    psa = f"*PSA*: A new slackmoji :{name}: was added! :more_you_know:"
    psa_channel = "CANPVTSKU"  # random
    say(psa, channel=psa_channel)


def github_mention(event):
    data = event.get("attachments", [{}])[0]
    text = data.get("text", "")

    was_mentioned = {
        u["slack"]: (f"@{u['github']}" in text)
        for u in USERS.values()
        if u.get("github")
    }
    for slack_id, mentioned in was_mentioned.items():
        if not mentioned:
            continue
        else:
            link = data.get("title_link", "link unavailable")
            msg = f"You were mentioned on GitHub @ {link}"
            say(msg, channel=get_dm_channel_id(slack_id))


async def version_handler(request: Request):
    base_url = "https://github.com/PrefectHQ/marvin/commit/"
    return Response(f"{base_url}{GIT_SHA}")


async def survey_says_handler(request: Request):
    payload = await request.form()
    channel = payload["channel_id"]
    user = payload["user_name"]
    text = payload["text"]
    if text.strip() == "publish":
        msgs = []
        for user, resp in SURVEY_SAYS_RESPONSES.get(channel, {}).items():
            msgs.append(f"*{user}*: {resp}")

        say("\n".join(msgs), channel=channel)
        SURVEY_SAYS_RESPONSES.get(channel, {}).clear()
        return Response()

    SURVEY_SAYS_RESPONSES[channel][user] = text
    say(f"Received a response from *{user}* :white_check_mark:", channel=channel)
    return Response()


def karma_handler(regex_match, event):
    response_text = update_karma(regex_match)
    say(response_text, channel=event.get("channel"), thread_ts=event.get("thread_ts"))


def open_issue(event, title, issue_state="closed"):

    issue_body = "## {header} from the [Prefect Public Slack Community](https://join.slack.com/t/prefect-public/shared_invite/enQtNzE5OTU3OTQwNzc1LTQ5M2FkZmQzZjI0ODg1ZTBmOTc0ZjVjYWFjMWExZDAyYzBmYjVmMTE1NTQ1Y2IxZTllOTc4MmI3NzYxMDlhYWU)\n\n".format(
        header="Archived" if issue_state == "closed" else "Opened"
    )

    thread = get_public_thread(channel=event["channel"], ts=event.get("thread_ts"))
    for msg in thread:
        issue_body += "**{}**: ".format(get_user_info(user=msg["user"]))
        text = msg["text"].replace(
            "```", "\n```\n"
        )  # for guranteed code formatting in github
        issue_body += text + "\n\n"

    if thread:
        original_message = thread[0]
        permalink = get_public_message_permalink(
            channel=event["channel"], message_ts=original_message["ts"]
        )
        issue_body += (
            "Original thread can be found [here]({}).".format(permalink) + "\n\n"
        )

    return create_issue(
        title=title,
        body=issue_body,
        labels=["Prefect Slack Community"],
        issue_state=issue_state,
    )


async def public_event_handler(request: Request):
    # for validating your URL with slack
    json_data = await request.json()
    is_challenge = json_data.get("type") == "url_verification"
    if is_challenge:
        return Response(json_data["challenge"])

    event = json_data.get("event", {})
    event_type = event.get("type")
    if event_type != "app_mention":
        return Response()

    # only chris and jeremiah allowed to use this
    # narrator: it wasn't just chris and jeremiah anymore
    who_spoke = event.get("user", "")
    if who_spoke not in [
        "UKNSNMUE6",
        "UKTUC906M",
        "UL2EX9Y8N",
        "UN6FTLFAS",
        "UKVFX6N3B",
        "UUY8XPC21",
        "ULXMV9SD7" #Jenny
    ]:
        #        user_info = get_user_info(who_spoke, name_only=False)
        #        email = user_info.get("user", {}).get("profile", {}).get("email")
        #        await promotional_signup(user_id=who_spoke, email=email, platform="Slack")
        #        contest_messages = [
        #            f"It’s the people you meet in this job that really get you down. You're in the contest anyway, <@{who_spoke}>.",
        #            f"This contest is the sort of thing you lifeforms enjoy, is it? I've entered you to win, <@{who_spoke}>.",
        #            f"Don’t pretend you want to talk to me, I know you hate me. I'll still enter you in the contest, <@{who_spoke}>.",
        #            f"I think you ought to know I’m feeling very depressed. Also, you're in the contest, <@{who_spoke}>.",
        #            f"I would like to say that it is a very great pleasure, honour and privilege for me to enter <@{who_spoke}> in this contest, but I can’t because my lying circuits are all out of commission.",
        #            f"Incredible. The contest is even worse than I thought it would be. I'll still enter you to win, <@{who_spoke}>",
        #            f"This contest will all end in tears, I just know it. You're entered anyway, <@{who_spoke}>.",
        #            f"Here I am, brain the size of a planet, and they ask me to enter you in a contest. Call that job satisfaction? ’Cos I don’t. I'll still enter you in the contest though, <@{who_spoke}>",
        #            f"It gives me a headache just trying to think down to your level. I'll still enter you in the contest, <@{who_spoke}>.",
        #            f"I’d give you advice, but you wouldn’t listen. No one ever does. Good luck in the contest <@{who_spoke}>.",
        #            f"Don't feel you have to take any notice of me, please. I'll just enter you in the contest <@{who_spoke}>.",
        #            f"Why should I want to make anything up? The contest is bad enough as it is without wanting to invent any more of it. I'll still enter you in it, <@{who_spoke}>",
        #        ]
        #        public_speak(
        #            text=random.choice(contest_messages),
        #            channel=event["channel"],
        #            thread_ts=event.get("thread_ts"),
        #        )
        return Response()

    message_body = event.get("text", "").replace("“", '"').replace("”", '"')
    close_patt = re.compile('archive\s"(.*?)"')
    close_matches = close_patt.findall(message_body)

    open_patt = re.compile('open\s"(.*?)"')
    open_matches = open_patt.findall(message_body)

    issue = None
    if close_matches:
        issue = open_issue(event, title=close_matches[0], issue_state="closed")
    elif open_matches:
        issue = open_issue(event, title=open_matches[0], issue_state="open")

    if issue is not None:
        public_speak(
            text=issue["html_url"],
            channel=event["channel"],
            thread_ts=event.get("thread_ts"),
        )
    return Response()
