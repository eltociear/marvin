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
    PUBLIC_TOKEN,
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
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "welcome.md"), "r") as f:
    WELCOME_MSG = f.read()

karma_regex = re.compile(r"^(.+[^\s])(\+{2}|\-{2})(\s*|$)$")


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
    elif event_type == "message" and event.get("channel") == "CCASU5P2R":
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
            link = data.get("title", "<https://github.com/PrefectHQ|").split("|", 1)[0]
            first_line = text.split("\n")[0] + " ..."
            msg = f"{link}|You were mentioned on GitHub> (preview):\n\n> {first_line}"
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


def build_issue_body(event, issue_state="open"):
    """Collect and format a slack thread to be archived as an issue"""

    header = "Archived" if issue_state == "closed" else "Opened"
    issue_body = f"## {header} from the [Prefect Public Slack Community](https://prefect.io/slack)\n\n"

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
    return issue_body


def get_create_issue_kwargs(event):
    """Get args to pass to `create_issue`. Returns `None` if no issue should be created

    Responds to:

    - 'archive "issue title"'
    - 'open "issue title"'
    - 'open "issue title" in repo' (where repo is one of {core, prefect, server, ui})
    """
    body = event.get("text", "").replace("“", '"').replace("”", '"').strip()
    message_types = [
        (r'archive\s+"(.*?)"', "closed", "prefect"),
        (r'open\s+"(.*?)"\s+in\s+(.*)', "open", None),
        (r'open\s+"(.*?)"', "open", "prefect"),
    ]
    for pattern, issue_state, repo in message_types:
        matches = re.findall(pattern, body)
        if matches:
            if repo is None:
                title, repo = matches[0]
            else:
                title = matches[0]
            break
    else:
        # No pattern matches
        return None

    repo = repo.lower().strip()
    if repo == "core":
        repo = "prefect"
    if repo not in {"prefect", "ui", "server"}:
        # Not a valid repo
        return None

    issue_body = build_issue_body(event, issue_state=issue_state)

    return {
        "title": title,
        "body": issue_body,
        "issue_state": issue_state,
        "labels": ["Prefect Slack Community"],
        "repo": repo,
    }


async def public_event_handler(request: Request):
    # for validating your URL with slack
    json_data = await request.json()
    is_challenge = json_data.get("type") == "url_verification"
    if is_challenge:
        return Response(json_data["challenge"])

    event = json_data.get("event", {})
    event_type = event.get("type")

    # for now, sending Chris and Kevin a DM to test the hook
    if event_type == "team_join":
        user_info = event.get("user", {})
        msg = "*New user signup:*```{}```".format(
            str(
                {
                    "name": user_info.get("name", "unknown"),
                    "real_name": user_info.get("real_name", "unknown"),
                }
            )
        )
        public_speak(msg, channel="DM1LRQH96")  # Chris DM
        public_speak(msg, channel="D01RXPH5NP9")  # Kevin DM

        # Welcome message to user
        user_id = user_info.get("id")
        name = user_info.get("name", "unknown")
        channel = get_dm_channel_id(user_id, PUBLIC_TOKEN)
        msg = WELCOME_MSG.replace("@user!", f"@{name}!")
        public_speak(msg, channel=channel)

        return Response()

    if event_type != "app_mention":
        return Response()

    # only chris and jeremiah allowed to use this
    # narrator: it wasn't just chris and jeremiah anymore
    who_spoke = event.get("user", "")
    if who_spoke not in [
        "UKNSNMUE6",  # Chris
        "UKTUC906M",  # Jeremiah
        "UN6FTLFAS",  # Nicholas
        "UKVFX6N3B",
        "UUY8XPC21",
        "U01CEUST9B5",  # Michael
        "U011EKN35PT",  # Jim
        "ULXMV9SD7",  # Jenny
        "U01SRTRJC0Y",  # Zach
        "U01QEJ9PP53",  # Kevin
        "U02EJ7FVCR5", # Evan
        "U02FNMJB05N", # Craig
        "U02GADJLAJE", # Anna
        "U02GDE5EQ68", # Josh
        "U02H0TR3HQQ", # Nate
        "U02GG396GN8", # George
        "U02GPSFNQSD", # Alex
        "U02GDE4SK7E", # James
        "U02GPSFVBUZ", # Jean
        "U02GF2MP605" # Kalise
    ]:
        return Response()

    kwargs = get_create_issue_kwargs(event)
    if kwargs is not None:
        issue = create_issue(**kwargs)
        if issue is not None:
            public_speak(
                text=issue["html_url"],
                channel=event["channel"],
                thread_ts=event.get("thread_ts"),
            )
    return Response()
