import asyncio
import json
import os
import random
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import requests
from starlette.requests import Request
from starlette.responses import Response

from marvin.utilities import get_dm_channel_id, get_users, say, promotional_signup

MARVIN_ACCESS_TOKEN = os.environ.get("MARVIN_ACCESS_TOKEN")


def create_issue(title, body, labels=None, issue_state="open"):
    url = "https://api.github.com/repos/PrefectHQ/prefect/issues"
    headers = {"AUTHORIZATION": f"token {MARVIN_ACCESS_TOKEN}"}
    issue = {"title": title, "body": body, "labels": labels or []}
    resp = requests.post(url, data=json.dumps(issue), headers=headers)
    if issue_state == "closed":
        number = resp.json()["number"]
        params = {"state": "closed"}
        resp = requests.patch(
            url + f"/{number}", data=json.dumps(params), headers=headers
        )
        return resp.json()
    else:
        return resp.json()


async def cloud_github_handler(request: Request):
    payload = await request.json()
    pr_data = payload.get("pull_request", {})
    labels = [lab.get("id", 0) for lab in pr_data.get("labels", [])]
    if 1_163_480_691 in labels and payload.get("action") == "closed":
        was_merged = pr_data.get("merged", False)
        pr_link = pr_data.get("html_url")
        if was_merged and pr_link is not None:
            body = f"See {pr_link} for more details"
            issue = create_issue(
                title="Cloud PR references Core",
                body=body,
                labels=["cloud-integration-notification"],
            )
    return Response()


@lru_cache(maxsize=1024)
def make_pr_comment(pr_num, body):
    url = f"https://api.github.com/repos/PrefectHQ/prefect/issues/{pr_num}/comments"
    headers = {"AUTHORIZATION": f"token {MARVIN_ACCESS_TOKEN}"}
    comment = {"body": body}
    resp = requests.post(url, data=json.dumps(comment), headers=headers)
    if resp.status_code == 201:
        return Response()


@lru_cache(maxsize=1024)
def notify_chris(pr_num):
    url = f"https://github.com/PrefectHQ/prefect/pull/{pr_num}"
    txt = f":tada: :tada: NEW CONTRIBUTOR PR: {url} :tada: :tada:"
    channel = get_dm_channel_id(get_users().get("chris"))
    say(txt, channel=channel)


async def core_promotion_handler(request: Request):

    payload = await request.json()
    comment = payload.get("comment", {}).get("body")
    if "@marvin-robot" in comment:
        user = payload.get("sender", {}).get("login")
        link = payload.get("issue", {}).get("html_url")
        num = payload.get("issue", {}).get("number")
        await promotional_signup(user_id=user, link=link, platform="GitHub")
        contest_messages = [
            f"It’s the people you meet in this job that really get you down. You're in the contest anyway, @{user}.",
            f"This contest is the sort of thing you lifeforms enjoy, is it? I've entered you to win, @{user}.",
            f"Don’t pretend you want to talk to me, I know you hate me. I'll still enter you in the contest, @{user}.",
            f"I think you ought to know I’m feeling very depressed. Also, you're in the contest, @{user}.",
            f"I would like to say that it is a very great pleasure, honour and privilege for me to enter @{user} in this contest, but I can’t because my lying circuits are all out of commission.",
            f"Incredible. The contest is even worse than I thought it would be. I'll still enter you to win, @{user}",
            f"This contest will all end in tears, I just know it. You're entered anyway, @{user}.",
            f"Here I am, brain the size of a planet, and they ask me to enter you in a contest. Call that job satisfaction? ’Cos I don’t. I'll still enter you in the contest though, @{user}",
            f"It gives me a headache just trying to think down to your level. I'll still enter you in the contest, @{user}.",
            f"I’d give you advice, but you wouldn’t listen. No one ever does. Good luck in the contest @{user}.",
            f"Don't feel you have to take any notice of me, please. I'll just enter you in the contest @{user}.",
            f"Why should I want to make anything up? The contest is bad enough as it is without wanting to invent any more of it. I'll still enter you in it, @{user}",
        ]
        make_pr_comment(num, random.choice(contest_messages))
    return Response()


async def core_github_handler(request: Request):
    actions = ["opened", "review_requested"]
    associations = ["FIRST_TIME_CONTRIBUTOR", "FIRST_TIMER", "NONE"]

    payload = await request.json()
    pr_data = payload.get("pull_request", {})
    if (
        pr_data.get("author_association", "").upper() in associations
        and payload.get("action", "").lower() in actions
    ):
        pr_num = pr_data.get("number")
        author = pr_data.get("user", {}).get("login")
        body = (
            "Here I am, brain the size of a planet and they ask me to welcome you to Prefect.\n\n"
            f"So, welcome to the community @{author}! :tada: :tada:"
        )
        try:
            notify_chris(pr_num)
        except:
            pass
        return make_pr_comment(pr_num, body)
    return Response()
