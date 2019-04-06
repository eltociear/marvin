import asyncio
import json
import os
import random
import requests
from concurrent.futures import ThreadPoolExecutor

from apistar.http import Body, Response


MARVIN_ACCESS_TOKEN = os.environ.get("MARVIN_ACCESS_TOKEN")


def create_issue(title, body, labels=None):
    url = "https://api.github.com/repos/PrefectHQ/prefect/issues"
    headers = {"AUTHORIZATION": f"token {MARVIN_ACCESS_TOKEN}"}
    issue = {"title": title, "body": body, "labels": labels or []}
    resp = requests.post(url, data=json.dumps(issue), headers=headers)
    if resp.status_code == 201:
        return Response("")


async def cloud_github_handler(data: Body):
    payload = json.loads(data)
    pr_data = payload.get("pull_request", {})
    labels = [lab.get("id", 0) for lab in pr_data.get("labels", [])]
    if 1163480691 in labels and payload.get("action") == "closed":
        was_merged = pr_data.get("merged", False)
        pr_link = pr_data.get("html_url")
        if was_merged and pr_link is not None:
            body = f"See {pr_link} for more details"
            return create_issue(
                title="Cloud PR references Core",
                body=body,
                labels=["cloud-integration-notification"],
            )


def make_pr_comment(pr_num, body):
    url = f"https://api.github.com/repos/PrefectHQ/prefect/issues/{pr_num}/comments"
    headers = {"AUTHORIZATION": f"token {MARVIN_ACCESS_TOKEN}"}
    comment = {"body": body}
    resp = requests.post(url, data=json.dumps(comment), headers=headers)
    if resp.status_code == 201:
        return Response("")


async def core_github_handler(data: Body):
    payload = json.loads(data)
    pr_data = payload.get("pull_request", {})
    if pr_data.get("author_association").upper() == "FIRST_TIME_CONTRIBUTOR":
        pr_num = pr_data.get("number")
        author = pr_data.get("user", {}).get("login")
        body = (
            "Here I am, brain the size of a planet and they ask me to welcome you to Prefect.\n\n"
            f"So, welcome to the community @{author}! :tada: :tada:"
        )
        return make_pr_comment(pr_num, body)
