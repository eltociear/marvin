import asyncio
import json
import os
import random
import requests
from concurrent.futures import ThreadPoolExecutor

from apistar.http import Body, Response


MARVIN_ACCESS_TOKEN = os.environ.get("MARVIN_ACCESS_TOKEN")


def create_issue(title, body, labels=None):
    url = "https://api.github.com/repos/PrefectHQ/marvin/issues"
    headers = {"AUTHORIZATION": f"token {MARVIN_ACCESS_TOKEN}"}
    issue = {"title": title, "body": body, "labels": labels or []}
    resp = requests.post(url, data=json.dumps(issue), headers=headers)
    if resp.status_code == 201:
        return Response("")


async def github_handler(data: Body):
    payload = json.loads(data)
    pr_data = payload.get("pull_request", {})
    labels = [lab.get("name", "").lower() for lab in pr_data.get("labels", [])]
    if "core" in labels and payload.get("action") == "closed":
        pr_link = pr_data.get("html_url")
        if pr_link is not None:
            body = f"See {pr_link} for more details"
            return create_issue(
                title="Cloud PR references Core",
                body=body,
                labels=["cloud-integration-notification"],
            )
